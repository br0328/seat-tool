
""" Database Table Schemas
"""

schemas = {
    'comment': '''
        CREATE TABLE IF NOT EXISTS tbl_comment (
            tid INT NOT NULL,
            mid INT NOT NULL,
            cid INT NOT NULL,
            val TEXT,
            PRIMARY KEY (tid, mid, cid)
        )
        ''',

    'person': '''    
        CREATE TABLE IF NOT EXISTS tbl_person (
            mid INT NOT NULL,
            surname TEXT NOT NULL,
            forename TEXT NOT NULL,
            branch TEXT NOT NULL,
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
            val INT,
            PRIMARY KEY (mid, eid)
        )
        ''',
    
    'person_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_match (
            mid INT NOT NULL,
            val1 INT,
            val2 INT,
            val3 INT,
            val4 INT,
            val5 INT,
            PRIMARY KEY (mid)
        )
        ''',
    
    'person_no_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_no_match (
            mid INT NOT NULL,
            val1 INT,
            val2 INT,
            val3 INT,
            val4 INT,
            val5 INT,
            PRIMARY KEY (mid)
        )
        ''',
    
    'person_never_match': '''    
        CREATE TABLE IF NOT EXISTS tbl_person_never_match (
            mid INT NOT NULL,
            val1 INT,
            val2 INT,
            val3 INT,
            val4 INT,
            val5 INT,
            val6 INT,
            val7 INT,
            val8 INT,
            val9 INT,
            val10 INT,
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
            val2 TEXT,
            val3 TEXT,
            val4 TEXT,
            val5 TEXT,
            val6 TEXT,
            val7 TEXT,
            val8 TEXT,
            val9 TEXT,
            val10 TEXT,
            display INT NOT NULL,
            PRIMARY KEY (neid)
        )
        '''
}
