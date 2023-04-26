            Cloud Outage Study DB public
            =============================

how to use COS-public?
-----------------------

1. docs/classifications.pdf
    
    Classifications.pdf is guideline for our tags classification in
    this cloud outage study. the classification document consists of
    Outage type(p-), Outage duration (-t), Root causes (r-), implication 
    (t-), and patch or fix (f-). You will find those tags on each 
    system under raw-public folder.

2. script-public/genhtml.py

    Genhtml.py script is helping you to filter and generate an html
    that contains the issues' table. There are six options systems
    name that can be used on this script, the systems are cassandra,
    flume, hbase, hdfs, mapreduce and zookeeper. Moreover, you can also
    filter the issue based on tags (find more available options on 
    valid-tags.txt). Here are examples to run the genhtml
    script.

    - Filter by service(s) name only.
        Command: ./genhtml.py facebook box                    
    
    - Filter by tag(s) only.
        Command: ./genhtml.py i-perf

    - Filter by system(s) and tag(s).
        Command: ./genhtml.py facebook r-bug i-perf
     
4. raw/*.txt

    These raw files contain the issue entries and our annotations. 
    To perform more advanced analyses, you can write python scripts that
    parse these raw files. 

