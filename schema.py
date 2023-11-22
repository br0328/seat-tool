
schemas = {
    'person': '''    
        CREATE TABLE IF NOT EXISTS tbl_person (
            mid INT NOT NULL,
            surname TEXT NOT NULL,
            forename TEXT NOT NULL,
            branch INT NOT NULL,
            display INT NOT NULL,
            PRIMARY KEY (mid)
        )
        ''',
    
    'event': '''    
        CREATE TABLE IF NOT EXISTS tbl_event (
            eid INT NOT NULL,
            title TEXT NOT NULL,
            display INT NOT NULL,
            PRIMARY KEY (eid)
        )
        ''',

    'person_event': '''
        CREATE TABLE IF NOT EXISTS tbl_person_event (
            mid INT NOT NULL,
            eid INT NOT NULL,
            val INT NOT NULL,
            PRIMARY KEY (mid, eid)
        )
        ''',
    
    'person_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_match (
            mid INT NOT NULL,
            val1 INT NOT NULL,
            val2 INT NOT NULL,
            val3 INT NOT NULL,
            val4 INT NOT NULL,
            val5 INT NOT NULL,
            PRIMARY KEY (mid)
        )
        ''',
    
    'person_no_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_no_match (
            mid INT NOT NULL,
            val1 INT NOT NULL,
            val2 INT NOT NULL,
            val3 INT NOT NULL,
            val4 INT NOT NULL,
            val5 INT NOT NULL,
            PRIMARY KEY (mid)
        )
        ''',
    
    'person_never_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_never_match (
            mid INT NOT NULL,
            val1 INT NOT NULL,
            val2 INT NOT NULL,
            val3 INT NOT NULL,
            val4 INT NOT NULL,
            val5 INT NOT NULL,
            val6 INT NOT NULL,
            val7 INT NOT NULL,
            val8 INT NOT NULL,
            val9 INT NOT NULL,
            val10 INT NOT NULL,
            PRIMARY KEY (mid)
        )
        ''',
    
    'person_selection': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_selection (
            mid INT NOT NULL,
            val INT NOT NULL,
            PRIMARY KEY (mid)
        )
        ''',
    
    'new_event': '''    
        CREATE TABLE IF NOT EXISTS tbl_new_event (
            neid INT NOT NULL,
            val1 TEXT NOT NULL,
            val2 TEXT NOT NULL,
            val3 TEXT NOT NULL,
            val4 TEXT NOT NULL,
            val5 TEXT NOT NULL,
            val6 TEXT NOT NULL,
            val7 TEXT NOT NULL,
            val8 TEXT NOT NULL,
            val9 TEXT NOT NULL,
            val10 TEXT NOT NULL,
            PRIMARY KEY (neid)
        )
        '''
}
