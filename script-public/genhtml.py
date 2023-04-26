#!/usr/bin/python

"""A script that generate a table in html for any raw tags.

Usage:

newgenhtml.py [tagcode] [sysname]

Ouput:
/tmp/search.html

Example:
search.py mapreduce dc-d
"""

#library
import os, re, sys, subprocess
# import envoy
 
# get key of dict from value of dict
def get_key_from_value(my_dict, v):
    for key,value in my_dict.items():
        if value == v:
            return key
    return None

# # List of names who has discussed an issue
WHO = []

SYSTEMS = {} 
metadata = open('categories.txt', 'r')
for line in metadata.readlines():
  if line.startswith('#') or len(line.split())<3:
    continue
  data = line.split()
  SYSTEMS[data[1].lower()] = data[2].lower()

# Systems name - shorten name
# 'skype',
# 'wechat',
# 'whatsapp',
# 'amazon-com', 
# 'ebay',
# 'gmail',
# 'm-hotmail',
# 'ymail',
# 'psnetwork',
# 'xbox-live',
# 'amazon-ebs',
# 'amazon-ec2',
# 'amazon-rds',
# 'gappengine',
# 'm-azure', 
# 'rackspace',
# 'gdocs',
# 'm-office365',     
# 'salesforce',
# 'facebook',
# 'gplus',
# 'instagram',
# 'twitter',
# 'apple-icloud',            
# 'box',
# 'dropbox',
# 'gdrive',
# 'm-skydrive',     
# 'netflix',
# 'youtube',
# ]

# Systems to check
CHECKSYSTEMS = []
           
# Type of tags in all systems
TAGFILTERS = []
# Tags to filter
CHECKTAGFILTERS = []

# Various aspects of a issue
DESC = 'desc'  # General description
COMP = 'comp'  # Component, e.g., ipc, spec. exec.
TEST = 'test'  # Test to reproduce
FAULT = 'fault'   # Failure involved, e.g, slow disk, node crash
SPEC = 'spec'   # Checks that can catch the bug.
FIX = 'fix'   # Potential fixes
CAT = 'cat'  # Category of bug
IMPACT = 'impact'
TAX = 'tax'  # HG's taxonomy
JIRA_LINK='https://issues.apache.org/jira/browse/{id}'
SAME_SHADE_ROWS = 3  # We will alternate shading after a number of rows.

# Function - TAGFILTERS selection
# Todo : grab all kinds of tags from system raw txt and store it inside
#        TAGFILTERS
def parseTagFilters():
  for s in SYSTEMS:
    filename = '../raw-public/%s.txt' % s.lower()
    if not os.path.exists(filename):
      print '%s does not exist' % filename
      sys.exit(-1)
    rawfile = open(filename, 'r')
    # Start Parsing
    for rawline in rawfile:
      line = rawline.rstrip()
      if(not line.startswith('[')) and (len(line) > 1) and (not line.startswith('  ')) and (not line.startswith('>')) and (not line in TAGFILTERS) and (not ' ' in line):
        TAGFILTERS.append(line)

# Function - Parameter Selection
# Todo : discern which parameter is system parameter and which one is
#        tag filters parameter
def parameterSelection():
  Unknowntag = []
  check = {}
  check['systems'] = list()
  check['tagfilters'] = list()
  if len(sys.argv) == 1:
    help()
  if len(sys.argv) > 1:
    for s in sys.argv:
      if s != './genhtml.py':
          #print SYSTEMS
          valid = False
          if s.lower() in SYSTEMS:
            check['systems'].append(s.lower())
            valid = True        
          for availableTag in TAGFILTERS:
              availableTagComp = availableTag.split('-')
              checkTagComp = s.split('-')
              matchTag = True
              for i in range(len(checkTagComp)):
                if checkTagComp[i] != availableTagComp[i]:
                  matchTag = False
                  break
              if matchTag:
                valid = True
                check['tagfilters'].append(s)
              if valid:
                break
          if s.lower() not in SYSTEMS and s not in TAGFILTERS:
            Unknowntag.append(s) 
  if len(Unknowntag) > 0:
    print 'Error: Invalid parameter '+', '.join(Unknowntag) +  '. Please look at valid-tags.txt to find the valid tag(s)'
    sys.exit(-1)  
  if len(check['systems']) == 0:
    check['systems'] = SYSTEMS.keys()
  if len(check['tagfilters']) == 0 and len(check['systems']) == 0:
    check['systems'] = SYSTEMS.keys()

  return check


#--------------------------------------
#--------- Issue Data structure -------
#--------------------------------------
class Issue(object):
    """A class that represent each bug."""
    def __init__(self, idstr, title, system, counter):
        self.idstr = idstr
        self.title = title
        self.sys = system
        self.num = counter
        self.reviewers = []
        self.types = []
        self.priority = 99
        # Notes
        self.notes = {}  # mapping from description
        self.notes[DESC] = ''
        self.notes[COMP] = ''
        self.notes[TEST] = ''
        self.notes[FAULT] = ''
        self.notes[SPEC] = ''
        self.notes[FIX] = ''
        self.notes[CAT] = ''
        self.notes[IMPACT] = ''
        self.notes[TAX] = ''
        self.studentnotes = ''
        self.hgnotes = ''
        # tempory variable, for parsing purpose.
        self._tmp = ''
        self.link = []

    def isRelevant(self):
        """Return True if this bug is tagged."""
        return len(self.reviewers) > 0
      
    def toString(self):
        """For debugging purpose only."""
        s = ''
        s += '[%s][%s]\n' % (self.idstr, self.title)
        s += 'Reviewers: %s\n' % str(self.reviewers)
        s += 'Types: %s\n' % str(self.types)
        s += 'Priority: %d\n' % self.priority
        s += 'Desc: %s\n' % self.notes[DESC]
        s += 'Comp: %s\n' % self.notes[COMP]
        s += 'Test: %s\n' % self.notes[TEST]
        s += 'Fault: %s\n' % self.notes[FAULT]
        s += 'Spec: %s\n' % self.notes[SPEC]
        s += 'Fix: %s\n' % self.notes[FIX]
        s += 'Cat: %s\n' % self.notes[CAT]
        s += 'Impact: %s\n' % self.notes[IMPACT]
        s += 'Students: %s\n' % self.studentnotes
        s += 'HG: %s\n' % self.hgnotes
        return s

    def parseTags(self, line, parser):
        # Who, types, and pipeline aspect.
        m = parser.pw.match(line)
        if m:
            tag = m.group(1)
            temp = tag.split('-')
            whoTag = ''
            try:
              whoTag = temp[1]
            except:
              pass
            if whoTag in WHO and not whoTag in self.reviewers:
              self.reviewers.append(whoTag)
            elif tag == "http":
              self.link.append(line)
            else:
              self.types.append(tag)
        # Priority.
        m = parser.pd.match(line)
        if m:
            tag = m.group(0)
            temp = tag.split('-')
            if temp[0] != 'x' and temp[0] != 's':
              self.priority = int(m.group(1))
            # So lowest priority is 1 according to the script.
            if self.priority == 0:
                self.priority = 1

    def parseNotes(self, line):
        if line.startswith(' ' * 4):
            self._tmp += line
        if len(line.strip()) == 0:
            self.processNotes(self._tmp)
            self._tmp = ''

    def processNotes(self, note):
        if note == '':
            return
        if note.startswith(' ' * 6):
            note = note.lstrip()
            i = note.find(':')
            prefix = note[:i].lower()
            content = note[i+1:]
            if prefix in self.notes:
                self.notes[prefix] += content
            else:
                self.hgnotes += '<p> %s' % note
        elif note.startswith(' ' * 4):
            note = note.lstrip()
            i = note.find(':')
            prefix = note[:i].lower()
            content = note[i+1:]
            if prefix in self.notes:
                self.notes[prefix] += content
            else:
                self.studentnotes += '<p> %s' % note

    def getWhoSortKey(self):
        if 'hg' in self.reviewers:
            who = '1hg'
        elif 'sl' in self.reviewers:
            who = '2sl'
        else:
            who = '3students'
        return who

    def _getImage(self, check):
        if check:
            return '<img width=15 height=15 src="check.gif">'
        return '<img width=15 height=15 src="cross.gif">'

    def getSortKey(self):
        """Sort key to show in html files.
        People should write different getSortKey method if needed be.
        """
        #print SYSTEMS
        return '<b>%02d-%s-%s</b><br><br>%05d' \
            % (self.priority, self.getWhoSortKey(), SYSTEMS[self.sys],
               self.num)

    def getPrintSortKey(self, counter):
        """Sort key to show in html files.
        People should write different getSortKey method if needed be.
        """
        # link = JIRA_LINK.format(id=self.idstr)
        link = self.link[0]
        sysnum = '%s-%s' % (SYSTEMS[self.sys], self.idstr)
        title = '<a href=\"%s\" target="_blank"><font size=+1><b>%s</b></font>:'
        title += ' %s (%d)</a>'
        title = title % (link, sysnum, self.title, counter)
        discuss = ', '.join(self.reviewers)
            
        return '%s<br><br><br><i></i>' \
            % (title)



#--------------------------------------
#--------- Parse logic ----------------
#--------------------------------------
class Parser(object):
    """A class for parsing. It has info about project tag,
    and list of systems. This should be independent of how
    we print the table."""

    def __init__ (self, systems, tagfilter):
        """Constructor.

        Params:
        - systems: list of String, e.g, ['mapreduce', 'hdfs']
        - tagfilter: list of string, e.g, ['dc-d','sw-eh']
        """
        self.systems = systems
        self.tagfilter = tagfilter
        
        # A bunch of regex
        self.pt = re.compile('\[(.+)\]\[(.+)\]') # For title and description
        self.pw = re.compile('([a-zA-Z\-\d]+)') # For who and types.
        self.pd = re.compile('[a-zA-Z]+-(\d+)') # For priority.
        

    def parseSystem(self, system):
        """This function contains the parsing logic.

        Params:
        - system: String lower case, system name, e.g. 'mapreduce'.

        Return: a dict mapping issue->issue.sortedkey.
        """
        print 'Parsing %s' % system
        filename = '../raw-public/%s.txt' % system
        if not os.path.exists(filename):
            print '%s does not exist' % filename
            sys.exit(-1)
        rawfile = open(filename, 'r')
        issues = {}
        cur = None
        counter = 1
        # Start parsing.
        for line in rawfile:
            # agung: if title
            m = self.pt.match(line)
            if m:
                # Reach new issue, store last issue.
                if cur != None and self.passFilter(cur):
                  issues[cur] = cur.getSortKey()
                idstr = m.group(1) #idstr or date
                title = m.group(2) #headline
                try:
                    cur = Issue(idstr, title, system, counter)
                    cur.idstr
                    counter+=1
                except:
                    print 'Warning: bad form'
                    print line
                    # reset parsing
                    cur = None
            if cur != None:
                cur.parseTags(line, self)
                cur.parseNotes(line)
        # Outside for loop. Remember the last issue.
        if self.passFilter(cur):
            issues[cur] = cur.getSortKey()
        return issues

    def passFilter(self, issue):
        """Check issue types and compare it with tagfilter
        Return: bool True or False, whether issue pass all the filters or not
        """
        listedTags = 0
        for tag in self.tagfilter:
          for typ in issue.types:
            if typ.startswith(tag):
              listedTags += 1
              break

        if listedTags == len(self.tagfilter):
          return True
        else:
          return False
    
    def parse(self):
        """Parse all systems.
        Return: a dict mapping issue->issue.sortedkey.
        """
        issues = {}
        for system in self.systems:
            issues.update(self.parseSystem(system))
        return issues


#--------------------------------------
#--------- Create html file -----------
#--------------------------------------
class Printer(object):
    """Printing HTML utils. The logic to different table styles
    should be here. For instance, if people want new table format,
    they will add new methods here to write different format.
    """

    def __init__(self):
        """Constructor.

        """
        # # Prepare output dir.
        # if not os.path.exists('/tmp/jira'):
        #     os.system('mkdir /tmp/jira')
        os.system('cp html-files/* /tmp/')

    def printHtml(self, issues):
        """Generate /tmp/jira/[tagcode].html.

        Params:
        - issues: a map (not sorted) from issue->issue.sortkey"""
        out = open('/tmp/output.html', 'w')
        self.printHeader(out)
        self.printTableHeader(out)
        self.printTableBody(out, issues)
        self.printFooter(out)
        out.close()

    def printHeader(self, out):
        header = '<html>\n'
        header += ' <head>\n'
        header += '  <meta>\n'
        header += '  <link rel=StyleSheet href=coffee.css type=text/css>\n'
        header += ' </head>\n'
        header += ' <body style="margin:0px">\n'
        header += ' <table>\n'
        out.write(header)

    def printFooter(self, out):
        out.write('  </table>\n')
        out.write(' </body>\n')
        out.write('</html>\n')

    def pRowStart(self, out, i=0):
        if i == 0:
            out.write('    <tr>\n')
            return
        t = i % (2 * SAME_SHADE_ROWS)
        if t >=1 and t <= SAME_SHADE_ROWS:
            out.write('    <tr class=noshade>\n')
        else:
            out.write('    <tr class=shade>\n')

    def pRowEnd(self, out):
        out.write('    </tr>\n')

    def pCol(self, out, col):
        out.write('     <td>%s</td>\n' % col)

    def printColWidth(self, out):
        out.write('<colgroup>\n')
        out.write('<col span="1" style="width: 70%;">')  # Key & Title
        #out.write('<col span="1" style="width: 10%;">')  # Title
        out.write('<col span="1" style="width: 30%;">')  # Desc
        out.write('<col span="1" style="width: 30%;">')  # Moreinfo
        out.write('</colgroup>\n')

    def printTableHeader(self, out):
        self.printColWidth(out)
        out.write('    <thead>\n');
        self.pRowStart(out);
        self.pCol(out, 'Title')
        #self.pCol(out, 'Title')
        # self.pCol(out, 'Desc')
        self.pCol(out, 'Tags')
        self.pCol(out, 'Comment')
        self.pRowEnd(out);
        out.write('    </thead>\n');

    def printTableBody(self, out, issues):
        """Notes: for new table with different column,
        please create new method.

        Params:
        - issues: a map (not sorted) from issue->issue.sortkey"""
        out.write('   <tbody>\n')
        i = 0
        """sort issues by issue number desc"""
        for issue, sortkey in sorted(issues.items(), key=lambda x: x[1], reverse=True):
            # TODO: may be combine all of this to
            # issue.getPrintentry? 
            self.pRowStart(out, i)
            self.pCol(out, issue.getPrintSortKey(i))
            #link = JIRA_LINK.format(id=issue.idstr)
            #sysnum = '%s-%d' % (SYSTEMS[issue.sys], issue.num)
            #title = '<a href=\"%s\"><font size=+1><b>%s</b></font>:'
            #title += ' %s (%d)</a>'
            #title = title % (link, sysnum, issue.title, i)
            #self.pCol(out, title)
            desc = issue.notes[DESC]
            if len(issue.studentnotes) > 0:
                desc += '<p><b>Students:</b> %s' % issue.studentnotes
            # self.pCol(out, desc)
            more = ''
            if len(issue.types) > 0:
                more = '<p><b>Tags:</b> %s' % ', '.join(issue.types)
            if len(issue.notes[COMP]) > 0:
                more += '<p><b>Comp:</b> %s' % issue.notes[COMP]
            if len(issue.notes[IMPACT]) > 0:
                more += '<p><b>Impact:</b> %s' % issue.notes[IMPACT]
            if len(issue.notes[TEST]) > 0:
                more += '<p><b>Test:</b> %s' % issue.notes[TEST]
            if len(issue.notes[FAULT]) > 0:
                more += '<p><b>Fault:</b> %s' % issue.notes[FAULT]
            if len(issue.notes[SPEC]) > 0:
                more += '<p><b>Spec:</b> %s' % issue.notes[SPEC]
            if len(issue.notes[FIX]) > 0:
                more += '<p><b>Fix:</b> %s' % issue.notes[FIX]
            if len(issue.notes[CAT]) > 0:
                more += '<p><b>Cat:</b> %s' % issue.notes[CAT]
            self.pCol(out, more)
            hg = issue.hgnotes
            if len(issue.notes[TAX]) > 0:
                hg += '<p><b>Tax:</b> %s' % issue.notes[TAX]
            self.pCol(out, hg)
            i += 1
            self.pRowEnd(out)
        out.write('   </tbody>\n')
        print str(i) + " issues found..."
def help():
    print ""
    print ""
    print "---------------------------help-----------------------------------"
    print "usage:"
    print "   ./genhtml.py [service name|tags]"
    print ""
    print "Available options:"
    print "   Service only      : Filter issues by service names            "
    print "             Example : ./genhtml.py facebook                     "
    print "   tags only         : Filter issues by tags for all systems     "
    print "             Example : ./genhtml.py r-bug i-down                 "        
    print "   Service and tags  : Filter issues by tags and service names   "
    print "             Example : ./genhtml.py facebook r-bug box i-loss    "
    print ""
    print "valid services: see the available services options onsee categories.txt"
    print "valid tags    : see the available tags options on valid-tags.txt   "    
    print "------------------------------------------------------------------"
    print ""
    print ""
    
    sys.exit(-1)    



# main class
def main():
  # parser service list
  # print SYSTEMS
  parseTagFilters()
  check = parameterSelection()
  CHECKSYSTEMS = check['systems']
  CHECKTAGFILTERS = check['tagfilters']

  print 'System(s) that will be checked: ' + str(CHECKSYSTEMS)
  print 'Filter Tag(s): ' + str(CHECKTAGFILTERS)
  parser = Parser([s.lower() for s in CHECKSYSTEMS], CHECKTAGFILTERS)
  issues = parser.parse()
  printer = Printer()
  printer.printHtml(issues)
  
  print "Open in the browser.."
  subprocess.call("./openBrowser.sh", shell =True)
  print "Done"

if __name__ == '__main__':
    main()
