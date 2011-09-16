#!/usr/bin/env python
import argparse
import os
import mwclient
import ConfigParser
import string
import time
import datetime
import subprocess
import commands
import sys

mantid_initialized = False
#
## Edit page
#page = site.Pages['Commons:Sandbox']
#text = page.edit()
#print 'Text in sandbox:', text.encode('utf-8')
#page.save(text + u'\nExtra data', summary = 'Test edit')
#
## Printing imageusage
#image = site.Images['Example.jpg']
#print 'Image', image.name.encode('utf-8'), 'usage:'
#for page in image.imageusage():
#    print 'Used:', page.name.encode('utf-8'), '; namespace', page.namespace
#    print 'Image info:', image.imageinfo
#
## Uploading a file
#site.upload(open('file.jpg'), 'destination.jpg', 'Image description')

#======================================================================
def initialize(args):
    global site
    # Init site object
    print "Connecting to site mantidproject.org"
    site = mwclient.Site('www.mantidproject.org', path='/')
    print "Logging in."
    site.login(args.username, args.password) # Optional
    
    
#======================================================================
def initialize_Mantid():
    """ Start mantid framework """
    global mtd
    global mantid_initialized
    if mantid_initialized:   return
    sys.path.append(os.getcwd())
    import MantidFramework
    from MantidFramework import mtd
    mtd.initialise()
    mantid_initialized = True

    
    
    


#======================================================================
def make_property_table_line(propnum, p):
    """ Make one line of property table
    propnum :: number of the prop
    p :: Property object
    """
    out = ""
    # The property number
    out += "|" + str(propnum) + "\n"
    # Name of the property
    out += "|" + p.name + "\n"
    # Direction
    direction_string = ["Input", "Output", "InOut", "None"]
    out += "|" + direction_string[p.direction] + "\n"
    # Type (as string)
    out += "|" + str(p.type) + "\n"
    # Default?
    if (p.isValid == ""): #Nothing was set, but it's still valid = NOT mandatory
      out += "| " + str(p.getDefault) + "\n"
    else:
      out += "|Mandatory\n"
    # Documentation
    out += "|" + p.documentation.replace("\n", " ") + "\n"
    # End of table line
    out += "|-\n"
    return out
    
    
        
#======================================================================
def make_wiki(algo_name):
    """ Return wiki text for a given algorithm """ 
    initialize_Mantid()
    alg = mtd.createAlgorithm(algo_name)
    
    out = ""
    out += "== Summary ==\n\n"
    out += alg._ProxyObject__obj.getOptionalMessage().replace("\n", " ") + "\n\n"
    out += "== Properties ==\n\n"
    
    out += """{| border="1" cellpadding="5" cellspacing="0" 
!Order\n!Name\n!Direction\n!Type\n!Default\n!Description
|-\n"""

    # Do all the properties
    props = alg._ProxyObject__obj.getProperties()
    propnum = 1
    for prop in props:
        out += make_property_table_line(propnum, prop)
        propnum += 1
        
        
    # Close the table
    out += "|}\n\n"


    out += "== Description ==\n"
    out += "\n"
    desc = alg.getWikiDescription()
    if (desc == ""):
      out += "INSERT FULL DESCRIPTION HERE\n"
      print "Warning: missing wiki description for %s! Placeholder inserted instead." % algo_name
    else:
      out += desc + "\n"
    out += "\n"
    out += "[[Category:Algorithms]]\n"
    
    # All other categories
    categories = alg.categories()
    for categ in categories:
      out += "[[Category:" + categ + "]]\n"

    out +=  "{{AlgorithmLinks|" + algo_name + "}}\n"

    return out






#======================================================================
def find_property_doc(lines, propname):
    """ Search WIKI text to find a properties' documentation there """
    if len(lines) == 0:
        return ""
    n = 0
    for line in lines:
        if line.strip() == "|" + propname:
            doc = lines[n+4].strip()
            if len(doc)>1:
                doc = doc[1:]
            return doc
        n += 1
            
    return ""
    
#======================================================================
def find_section_text(lines, section):
    """ Search WIKI text to find a section text there """
    if len(lines) == 0:
        return ""
    n = 0
    for line in lines:
        if line.strip().startswith("== %s" % section):
            # Section started
            n += 1
            doc = ""
            # collect the documents till next section or the end 
            newline = lines[n]
            while not newline.strip().startswith('==') and not newline.strip().startswith('[[Category'):
                doc += newline + '\n'
                n += 1
                if n < len(lines):
                    newline = lines[n]
                else:
                    break
            return doc
        n += 1
            
    return ""
    
    
#======================================================================
def validate_wiki(args, algos):
    """ Look for any missing wiki pages / inconsistencies """
    missing = []
    
    for algo in algos:
        print "\n================= %s ===================" % algo
        
        # Check wiki page and download contents
        page = site.Pages[algo]
        wiki = page.edit()
        lines = []
        if len(wiki) == 0:
            print "- Algorithm wiki page for %s is MISSING!" % algo
            missing.append(algo)
        else:
            lines = wiki.split('\n')

        # Validate the algorithm itself
        alg = mtd.createAlgorithm(algo)
        summary = alg._ProxyObject__obj.getOptionalMessage()
        if len(summary) == 0: 
            print "- Summary is missing (in the code)."
            wikidoc = find_section_text(lines, "Summary")
            if args.show_missing: print wikidoc
            
        desc = alg._ProxyObject__obj.getWikiDescription()
        if len(desc) == 0: 
            print "- Wiki Description is missing (in the code)."
            if args.show_missing: print find_section_text(lines, "Description")
            
        props = alg._ProxyObject__obj.getProperties()
        for prop in props:
            if len(prop.documentation) == 0:
                print "- Property %s has no documentation/tooltip (in the code)." % prop.name,
                wikidoc = find_property_doc(lines, prop.name)
                if len(wikidoc) > 0:
                    print "Found in wiki"
                    if args.show_missing: print "   \"%s\"" % wikidoc
                else:
                    print "Not found in wiki."
            
    print "\n\n"
    print "Algorithms with missing wiki page:\n", " ".join(missing) 


#======================================================================
def do_algorithm(args, algo):
    print "Generating wiki page for %s" % (algo)
    global site
    contents = make_wiki(algo)
    
    print "Saving page to www.mantidproject.org/%s" % algo
    #Open the page with the name of the algo
    page = site.Pages[algo]
    text = page.edit()
    #print 'Text in page:', text.encode('utf-8')
    page.save(contents, summary = 'Bot: replace contents by auto_wiki.py script, using output from WikiMaker.' )

#======================================================================
if __name__ == "__main__":
    # First, get the config for the last settings
    config = ConfigParser.ConfigParser()
    config_filename = os.path.split(__file__)[0] + "/auto_wiki.ini"
    config.read(config_filename)
    defaultuser = ""
    defaultpassword = ""
    try:
        defaultuser = config.get("login", "username")
        defaultpassword = config.get("login", "password")
    except:
        pass
    
    parser = argparse.ArgumentParser(description='Generate the Wiki documentation for one '
                                      'or more algorithms, and updates the mantidproject.org website')
    
    parser.add_argument('algos', metavar='ALGORITHM', type=str, nargs='*',
                        help='Name of the algorithm(s) to generate wiki docs.')
    
    parser.add_argument('--user', dest='username', default=defaultuser,
                        help="User name, to log into the www.mantidproject.org wiki. Default: '%s'. This value is saved to a .ini file so that you don't need to specify it after." % defaultuser)

    parser.add_argument('--password', dest='password', default=defaultpassword,
                        help="Password, to log into the www.mantidproject.org wiki. Default: '%s'. Note this is saved plain text to a .ini file!" % defaultpassword)
    
    parser.add_argument('--validate', dest='validate_wiki', action='store_const',
                        const=True, default=False,
                        help="Validate algorithms' documentation. Validates them all if no algo is specified. Look for missing wiki pages, missing properties documentation, etc. using the list of registered algorithms.")
    
    parser.add_argument('--show-missing', dest='show_missing', action='store_const',
                        const=True, default=False,
                        help="When validating, pull missing in-code documentation from the wiki and show it.")

    args = parser.parse_args()
    
    # Write out config for next time
    config = ConfigParser.ConfigParser()
    config.add_section("login")
    config.set("login", "username", args.username)
    config.set("login", "password", args.password)
    f = open(config_filename, 'w')
    config.write(f)
    f.close()
    
    # Open the site
    initialize(args)
    initialize_Mantid()

    if args.validate_wiki:
        # Validate a few, or ALL algos
        algos = args.algos
        if len(algos) == 0:
            temp = mtd._getRegisteredAlgorithms(True)
            algos = [x for (x, version) in temp]
        validate_wiki(args, algos)
    else:
        for algo in args.algos:
            do_algorithm(args, algo)
        