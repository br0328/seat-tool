
from deap import base, creator, tools, algorithms
from pandas import DataFrame
from constant import *
from util import *
import numpy as np
import pandas as pd
import random
import math
import re

max_num_relevant_hist_events = 1000000  # This indicates the maximum number of historical events that should be taken into account when designing the seating arrangement
bestrafung_last_hist_event = -10000 # Punishment value at the last (most recent) historical event
bestrafung_rate = 0.9 # Rate at which the penalty of next historical events is reduced
num_sitzplaetze_tisch = 6  # Number of seats at a table
wb = None

best_satisfaction = None
best_individual = None
nomatch_value = -100000000  # Punishment value if two people sit at the same table even though this is not desired.
nevermatch_value = -100000000  # Punishment value if two people sit at the same table even though this is not desired.
match_value = 1000000 # Reward value for two people sitting at the same table if desired.
branchen_value = -100
num_generations = 1000

class Engine:
    def __init__(self, person_df, person_selection_df, person_event_df, person_match_df, person_no_match_df, person_never_match_df):
        merged_df = person_df.merge(person_selection_df, on = 'mid', how = 'inner')
        
        self.person_df = merged_df[merged_df['val'] > 0]
        self.person_event_df = person_event_df
        self.person_selection_df = person_selection_df
        self.person_match_df = person_match_df
        self.person_no_match_df = person_no_match_df
        self.person_never_match_df = person_never_match_df        
        self.df = None
        self.results = None
        self.df_personen = None  # initialisiere das DataFrame Attribut
        self.df_relations = None
        self.id_list = None
        self.df_bestr_tot = None
        self.df_satis_match = None
        self.df_satis_nomatch = None
        self.df_satis_nevermatch = None
        self.satisfaction_matrix = None
        self.df_satisfaction_matrix = None
        self.grouped_df = None
        self.num_persons = None
        self.num_tische = None
        self.gruppen_namen = None
        self.df_optimal_seating = None  # Dataframe containing the optimal assignment of people to tables.
        self.df_conflicts = None
        self.overall_score = 0

    #-----------------------------------------------------------
    # Calculation of the relation matrix: n*n matrix corresponding to the IDs of all registered people
    # A data frame of all relationships between all person IDs is created. In the column names and
    # Line names represent all person IDs. The content of this matrix consists of zeros.
    #-----------------------------------------------------------
    def calc_relations_matrix(self):
        # self.df_personen['Anmeldung'] = self.df_personen['Anmeldung'].fillna('') # Missing values (NaN) in the 'Registration' column of the DataFrame df_persons are replaced with an empty string ('').
        # self.df_personen_angemeldet = self.df_personen[self.df_personen['Anmeldung'] != '']  # Create a new DataFrame that contains only the rows that have an entry in the Login column
        # self.id_list = self.df_personen_angemeldet['ID'].tolist()  # List of all registered person IDs
        # self.df_relations = pd.DataFrame(0, index = self.id_list, columns = self.id_list) # Create a new DataFrame where the entries of the 'ID' column become the row names and the column names at the same time
        
        self.id_list = self.person_df['mid'].tolist() # List of all registered person IDs
        self.df_relations = pd.DataFrame(0.0, index = self.id_list, columns = self.id_list) # Create a new DataFrame where the entries of the 'ID' column become the row names and the column names at the same time

    #-----------------------------------------------------------
    # Function that penalizes associations of people who sat at the same table on a previous occasion.
    # receives the column name and the punishment value as an argument and returns the punishment matrix
    #-----------------------------------------------------------
    def bestrafungsmatrix(self, eid, bestrafungswert):    
        df_tmp = self.df_relations.copy()
        group_dict = self.person_event_df[self.person_event_df['eid'] == eid].set_index('mid')
        idx_list = group_dict.index.tolist()
        
        for id1 in idx_list:
            v = null_or(group_dict.loc[id1].val, -1)
            if v <= 0: continue
            
            for id2 in idx_list:
                if id1 == id2: continue # ignore cases where row and column values are the same
                                    
                if v == group_dict.loc[id2].val:
                    df_tmp.loc[id1, id2] = bestrafungswert
                    
        return df_tmp
    
    def calc_satisfaction_matrix(self):
        eid_list = sorted(list(set(self.person_event_df['eid'].tolist())), reverse = True)
        
        # Punishment matrix based on historical pairings
        num_hist_events = min(max_num_relevant_hist_events, len(eid_list))  # Depending on whether the maximum number of events we have defined or the effective number of available events is smaller.
        self.df_bestr_tot = self.df_relations.copy()  # A copy is created. All zeros
        
        for i in range(num_hist_events):
            bestrafungswert = bestrafung_last_hist_event * bestrafung_rate ** i
            self.df_bestr_tot = self.df_bestr_tot + self.bestrafungsmatrix(eid_list[i], bestrafungswert)
    
        # Forced pairings        
        personen_ids = self.person_df['mid'].tolist()
        self.df_satis_match = pd.DataFrame(np.zeros((len(personen_ids), len(personen_ids))), columns = personen_ids, index = personen_ids)
                
        for _, row in self.person_match_df.iterrows():
            for i in range(match_col_count):
                v = null_or(row[f"val{i + 1}"], 0)
                # Update the value in df_satis_match at the appropriate location
                if v in personen_ids:
                    self.df_satis_match.at[row['mid'], int(v)] = match_value
                    self.df_satis_match.at[int(v), row['mid']] = match_value
        
        # Forced non-matings
        self.df_satis_nomatch = pd.DataFrame(np.zeros((len(personen_ids), len(personen_ids))), columns = personen_ids, index = personen_ids)
        
        for _, row in self.person_no_match_df.iterrows():
            for i in range(no_match_col_count):
                v = null_or(row[f"val{i + 1}"], 0)
                # Update the value in df_satis_nomatch at the appropriate location
                if v in personen_ids:
                    self.df_satis_nomatch.at[row['mid'], int(v)] = nomatch_value
                    self.df_satis_nomatch.at[int(v), row['mid']] = nomatch_value
        
        # Forced never-matings
        self.df_satis_nevermatch = pd.DataFrame(np.zeros((len(personen_ids), len(personen_ids))), columns = personen_ids, index = personen_ids)
        
        for _, row in self.person_never_match_df.iterrows():
            for i in range(never_match_col_count):
                v = null_or(row[f"val{i + 1}"], 0)
                # Update the value in df_satis_nevermatch at the appropriate location
                if v in personen_ids:
                    self.df_satis_nevermatch.at[row['mid'], int(v)] = nevermatch_value
                    self.df_satis_nevermatch.at[int(v), row['mid']] = nevermatch_value

        # Industry pairings
        # Extract the “ID” and “Industry Categories” columns
        df_personen_angemeldet_branchen = self.person_df[['mid', 'branch']]
    
        # Create the second DataFrame with the same row and column names
        # Use np.zeros to create a matrix of zeros
        self.df_satis_branchen = pd.DataFrame(np.zeros((len(personen_ids), len(personen_ids))), columns = personen_ids, index = personen_ids)
    
        # Examine df1 and update df2 based on the joins
        for i in range(len(df_personen_angemeldet_branchen)):
            b = null_or(df_personen_angemeldet_branchen.iloc[i]['branch'], '')
            if b == '': continue
            
            idx = df_personen_angemeldet_branchen.iloc[i]['mid']
            
            for j in range(i + 1, len(df_personen_angemeldet_branchen)):
                if b == null_or(df_personen_angemeldet_branchen.iloc[j]['branch'], ''):
                    # Update the value in df2 at the appropriate location
                    self.df_satis_branchen.at[idx, df_personen_angemeldet_branchen.iloc[j]['mid']] = branchen_value
                    self.df_satis_branchen.at[df_personen_angemeldet_branchen.iloc[j]['mid'], idx] = branchen_value  # symmetrisch
    
        # Assembling all elements of the satisfaction matrix and converting it into a NumPy array        
        self.df_satisfaction_matrix = self.df_bestr_tot.copy() + self.df_satis_match.copy() + self.df_satis_nomatch.copy() + self.df_satis_nevermatch.copy() + self.df_satis_branchen.copy()        
        self.df_satisfaction_matrix = self.df_satisfaction_matrix.fillna(0)
        self.satisfaction_matrix = self.df_satisfaction_matrix.values  # Convert DataFrame to NumPy array
        
        print(self.df_satisfaction_matrix)

    #-----------------------------------------------------------
    # Calculation of number of tables and number of people per table
    #----------------------------------------------------------- 
    def calc_num_tables_num_persons(self):            
        self.num_persons = len(self.id_list)  # Number of people who have logged in
        self.num_tische = math.ceil(self.num_persons / num_sitzplaetze_tisch) # Number of tables (groups) necessary to meet the number of seats. Decimal fraction is rounded up to the nearest whole number.
        max_group_size = math.ceil(self.num_persons / self.num_tische)  # Maximum table size (max number of people at one table)
        min_group_size = max_group_size - 1       # Minimum table size (minimum number of people at a table)
        num_grosse_tische = self.num_persons - self.num_tische * min_group_size 
        num_kleine_tische = self.num_tische - num_grosse_tische
        group_sizes = np.array([max_group_size] * num_grosse_tische + [min_group_size] * num_kleine_tische)
    
        self.gruppen_namen = np.empty(self.num_persons)  
        start_index = 0
        
        for i, b in enumerate(group_sizes, start = 1):
            self.gruppen_namen[start_index : start_index + b] = i
            start_index += b  # This line has been added
            
        print(self.gruppen_namen)

    #-----------------------------------------------------------
    # optimization
    #----------------------------------------------------------- 
    
    # Evaluation function
    # This function needs to be reworked so that the respective permutation is distributed into groups accordingly
    # the group sizes so that the difference between the largest and smallest group is 1.
    def evaluate(self, individual):
        individual_np = np.array(individual)
        
        # Iterate over all tables
        total_satisfaction = 0
        
        for i in range(1, self.num_tische + 1):            
            # Indexing with numpy.where()
            indizes_am_gleichen_tisch = np.sort(individual_np[self.gruppen_namen == i])
    
            # The selected columns and rows
            selected_rows_columns = self.satisfaction_matrix[np.ix_(indizes_am_gleichen_tisch, indizes_am_gleichen_tisch)].copy()            
            sum_of_elements = np.sum(selected_rows_columns)            
            total_satisfaction += sum_of_elements
    
        return total_satisfaction,
    
    def optimisation(self):
        # Genetic algorithm parameters
        POPULATION_SIZE = 100
        CROSSOVER_RATE = 0.8
        MUTATION_RATE = 0.2
        NUM_GENERATIONS = num_generations
    
        # Create types for fitness and individuals
        creator.create("FitnessMax", base.Fitness, weights = (1.0,))  # The larger the value, the better the fitness
        creator.create("Individual", list, fitness = creator.FitnessMax)
    
        # Create functions to initialize individuals and population
        toolbox = base.Toolbox()
        toolbox.register("indices", random.sample, range(self.num_persons), self.num_persons) # Here a random permutation of the numbers 0 to n is generated
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
        # Register the scoring function and genetic operators
        toolbox.register("mate", tools.cxPartialyMatched)
        toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", self.evaluate)
    
        # Create the population and run the genetic algorithm
        population = toolbox.population(n = POPULATION_SIZE)
        result, _ = algorithms.eaSimple(population, toolbox, cxpb = CROSSOVER_RATE, mutpb = MUTATION_RATE, ngen = NUM_GENERATIONS, verbose = False)
    
        # Find the best solution and calculate satisfaction
        best_individual = tools.selBest(result, k=1)[0]
        best_satisfaction = self.evaluate(best_individual)[0]
    
        print("------------------------------------------")
        print("Genetischer Algorithmus:")
        print('best_satisfaction', best_satisfaction)
        print('best_individual', best_individual)
        
        self.df_optimal_seating = pd.DataFrame({
            'Personen': best_individual,
            'Val': self.gruppen_namen.astype(int)
        })
        self.df_optimal_seating = self.df_optimal_seating.sort_values(by='Personen', ascending=True)    
        self.df_optimal_seating['ID'] = self.id_list
            
        print('df_optimal_seating \n', self.df_optimal_seating)
        
        self.overall_score = best_satisfaction

    # Check which historical pairings are undesirably recurring
    #---------------------------------------------------------------------------------   
    def show_conflicts(self):    
        df_bestr_tot_relevant = self.df_bestr_tot.copy()
    
        # Converting the df1 to an ID-to-group mapping
        group_dict = {ID:group for group, IDs in self.grouped_df.items() for ID in IDs}
    
        # Check each entry in df2 and set it to 0 if the IDs are not in the same group
        for index in self.df_bestr_tot.index:
            for column in self.df_bestr_tot.columns:
                # Skip the case when the ID is combined with itself
                if index == column: continue
                
                # If the IDs are not in the same group, set the value to 0
                if group_dict.get(index) != group_dict.get(column):
                    df_bestr_tot_relevant.at[index, column] = 0
    
        stacked_df_bestr_tot_relevant = df_bestr_tot_relevant.stack() # Convert df_bestr_tot_relevant into a series object
        df_bestr_tot_relevant_non_zero = stacked_df_bestr_tot_relevant.reset_index() # Create a DataFrame from the Series object
        df_bestr_tot_relevant_non_zero.columns = ['ID1', 'ID2', 'Value'] # Rename the columns
        df_bestr_tot_relevant_non_zero[['ID1', 'ID2']] = np.sort(df_bestr_tot_relevant_non_zero[['ID1', 'ID2']].values, axis=1)  # Sort the 'ID1' and 'ID2' columns
        df_bestr_tot_relevant_non_zero = df_bestr_tot_relevant_non_zero[df_bestr_tot_relevant_non_zero['Value'] != 0]   # Only keep the rows where 'Value' is non-zero
        df_bestr_tot_relevant_non_zero.drop_duplicates(inplace=True) # Remove duplicates
        df_bestr_tot_relevant_non_zero['Konflikt-Art'] = 'Wiederholte Paarung'
    
        # Check which undesirable pairings were still implemented
        #---------------------------------------------------------------------------------
        self.df_satis_nomatch.index.name = None
        self.df_satis_nomatch.columns.name = None
    
        df_satis_nomatch_relevant = self.df_satis_nomatch.copy()
        group_dict = {ID:group for group, IDs in self.grouped_df.items() for ID in IDs}
    
        # Check each entry in df2 and set it to 0 if the IDs are not in the same group
        for index in self.df_satis_nomatch.index:
            for column in self.df_satis_nomatch.columns:
                # Skip the case when the ID is combined with itself
                if index == column: continue
                # If the IDs are not in the same group, set the value to 0
                if group_dict.get(index) != group_dict.get(column):
                    df_satis_nomatch_relevant.at[index, column] = 0
    
        stacked_df_satis_nomatch_relevant = df_satis_nomatch_relevant.stack()   # Convert df_bestr_tot_relevant into a series object
        df_satis_nomatch_relevant_non_zero = stacked_df_satis_nomatch_relevant.reset_index()   # Create a DataFrame from the Series object
        df_satis_nomatch_relevant_non_zero.columns = ['ID1', 'ID2', 'Value']   # Rename the columns
        #print(df_satis_nomatch_relevant_non_zero.columns)
        
        df_satis_nomatch_relevant_non_zero[['ID1', 'ID2']] = np.sort(df_satis_nomatch_relevant_non_zero[['ID1', 'ID2']].values, axis=1)  # Sort the 'ID1' and 'ID2' columns
        df_satis_nomatch_relevant_non_zero = df_satis_nomatch_relevant_non_zero[df_satis_nomatch_relevant_non_zero['Value'] != 0]   # Only keep the rows where 'Value' is non-zero
        df_satis_nomatch_relevant_non_zero.drop_duplicates(inplace=True)   # Remove duplicates
        df_satis_nomatch_relevant_non_zero['Konflikt-Art'] = 'Unerwünschte No-match'
        
        # NEVER ___ Check which undesirable pairings were still implemented
        #---------------------------------------------------------------------------------
        self.df_satis_nevermatch.index.name = None
        self.df_satis_nevermatch.columns.name = None
    
        df_satis_nevermatch_relevant = self.df_satis_nevermatch.copy()
        group_dict = {ID:group for group, IDs in self.grouped_df.items() for ID in IDs}
    
        # Check each entry in df2 and set it to 0 if the IDs are not in the same group
        for index in self.df_satis_nevermatch.index:
            for column in self.df_satis_nevermatch.columns:
                # Skip the case when the ID is combined with itself
                if index == column: continue
                # If the IDs are not in the same group, set the value to 0
                if group_dict.get(index) != group_dict.get(column):
                    df_satis_nevermatch_relevant.at[index, column] = 0
    
        stacked_df_satis_nevermatch_relevant = df_satis_nevermatch_relevant.stack()   # Convert df_bestr_tot_relevant into a series object
        df_satis_nevermatch_relevant_non_zero = stacked_df_satis_nevermatch_relevant.reset_index()   # Create a DataFrame from the Series object
        df_satis_nevermatch_relevant_non_zero.columns = ['ID1', 'ID2', 'Value']   # Rename the columns
        #print(df_satis_nevermatch_relevant_non_zero.columns)
        
        df_satis_nevermatch_relevant_non_zero[['ID1', 'ID2']] = np.sort(df_satis_nevermatch_relevant_non_zero[['ID1', 'ID2']].values, axis=1)  # Sort the 'ID1' and 'ID2' columns
        df_satis_nevermatch_relevant_non_zero = df_satis_nevermatch_relevant_non_zero[df_satis_nevermatch_relevant_non_zero['Value'] != 0]   # Only keep the rows where 'Value' is non-zero
        df_satis_nevermatch_relevant_non_zero.drop_duplicates(inplace=True)   # Remove duplicates
        df_satis_nevermatch_relevant_non_zero['Konflikt-Art'] = 'Unerwünschte Never-match'
    
        # Check which desired pairings were not realized
        #---------------------------------------------------------------------------------
        self.df_satis_match.index.name = None
        self.df_satis_match.columns.name = None
    
        df_satis_match_relevant = self.df_satis_match.copy()
    
        # Converting the df1 to an ID-to-group mapping
        group_dict = {ID:group for group, IDs in self.grouped_df.items() for ID in IDs}
    
        # Check each entry in df2 and set it to 0 if the IDs are not in the same group
        for index in self.df_satis_match.index:
            for column in self.df_satis_match.columns:
                # Skip the case when the ID is combined with itself
                if index == column: continue
                
                # If the IDs are not in the same group, set the value to 0
                if group_dict.get(index) != group_dict.get(column):
                    df_satis_match_relevant.at[index, column] = 0
    
        df_satis_match_missed = self.df_satis_match - df_satis_match_relevant  # The missed (desired) pairings: The difference between all pairings that were desired and those that were realized.
        stacked_df_satis_match_missed = df_satis_match_missed.stack()   # Convert df_bestr_tot_relevant into a series object
    
        df_satis_match_missed_non_zero = stacked_df_satis_match_missed.reset_index()   # Create a DataFrame from the Series object
        df_satis_match_missed_non_zero.columns = ['ID1', 'ID2', 'Value']   # Rename the columns
        
        df_satis_match_missed_non_zero[['ID1', 'ID2']] = np.sort(df_satis_match_missed_non_zero[['ID1', 'ID2']].values, axis=1)  # Sort the 'ID1' and 'ID2' columns
        df_satis_match_missed_non_zero = df_satis_match_missed_non_zero[df_satis_match_missed_non_zero['Value'] != 0]   # Only keep the rows where 'Value' is non-zero
        df_satis_match_missed_non_zero.drop_duplicates(inplace=True)   # Remove duplicates
    
        df_satis_match_missed_non_zero['Konflikt-Art'] = 'Verpasste erwünschte Paarung'
        
        # Check which undesirable industry pairings were still implemented
        #---------------------------------------------------------------------------------
        self.df_satis_branchen.index.name = None
        self.df_satis_branchen.columns.name = None
    
        df_satis_branchen_relevant = self.df_satis_branchen.copy()   # A copy is created
    
        # Converting the df to an id-to-group mapping
        group_dict = {ID:group for group, IDs in self.grouped_df.items() for ID in IDs}
    
        # Check each entry in df2 and set it to 0 if the IDs are not in the same group
        for index in self.df_satis_branchen.index:
            for column in self.df_satis_branchen.columns:
                # Skip the case when the ID is combined with itself
                if index == column: continue
                
                # If the IDs are not in the same group, set the value to 0
                if group_dict.get(index) != group_dict.get(column):
                    df_satis_branchen_relevant.at[index, column] = 0
    
        stacked_df_satis_branchen_relevant = df_satis_branchen_relevant.stack()   # Convert df_bestr_tot_relevant into a series object    
        df_satis_branchen_relevant_non_zero = stacked_df_satis_branchen_relevant.reset_index()   # Create a DataFrame from the Series object
        df_satis_branchen_relevant_non_zero.columns = ['ID1', 'ID2', 'Value']   # Rename the columns
        #print(df_satis_branchen_relevant_non_zero.columns)
        
        df_satis_branchen_relevant_non_zero[['ID1', 'ID2']] = np.sort(df_satis_branchen_relevant_non_zero[['ID1', 'ID2']].values, axis=1)  # Sort the 'ID1' and 'ID2' columns
        df_satis_branchen_relevant_non_zero = df_satis_branchen_relevant_non_zero[df_satis_branchen_relevant_non_zero['Value'] != 0]   # Only keep the rows where 'Value' is non-zero
        df_satis_branchen_relevant_non_zero.drop_duplicates(inplace=True)   # Remove duplicates
        df_satis_branchen_relevant_non_zero['Konflikt-Art'] = 'Unerwünschte Branchen-Paarung'
    
        self.df_conflicts = pd.concat([
            df_bestr_tot_relevant_non_zero,
            df_satis_nomatch_relevant_non_zero,
            df_satis_nevermatch_relevant_non_zero,
            df_satis_match_missed_non_zero,
            df_satis_branchen_relevant_non_zero
        ])
        #print(self.df_conflicts)

    def show_groups(self):
        grouped = self.df_optimal_seating.groupby('Val')['ID'].apply(list)
        # Konvertieren zur DataFrame mit Event-Kategorien als Spalten
        self.grouped_df = pd.DataFrame(grouped.tolist(), index=grouped.index).T

    def calculate(self):
        self.calc_relations_matrix()
        self.calc_satisfaction_matrix()
        self.calc_num_tables_num_persons()
        self.optimisation()
        self.show_groups()
        self.show_conflicts()
        
        return (
                self.df_optimal_seating.rename(columns = {'ID': 'mid', 'Val': 'val'}),
                self.df_conflicts.rename(columns = {'ID1': 'id1', 'ID2': 'id2', 'Value': 'val', 'Konflikt-Art': 'conflict'}),
                self.overall_score
        )
