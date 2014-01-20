#!/usr/bin/env python
import argparse
import json
import os

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'

    from mumlife import utils
    from mumlife.engines import SearchEngine

    choices = [
        'get-age-bracket',          # Get age bracket from DoB
        'get-postcode-point',       # Get location point for postcode
        'get-postcodes-distance',   # Get distance between 2 postcodes
        'extract-tags',             # Extract tag from string
        'extract-flags',            # Extract flags from string
    ]
    parser = argparse.ArgumentParser(description="Mumlife Command-Line Test Tool")
    parser.add_argument('command', type=str, help='command to execute', choices=choices)
    parser.add_argument('arguments', type=str, nargs='*', help='command arguments')
    args = parser.parse_args()

    if args.command == 'get-age-bracket':
        try:
            dob = args.arguments[0]
        except IndexError:
            print ' >> ERROR - date of birth required; format: DD/MM/YYYY (e.g. 24/11/1978)'
            print
            parser.print_help()
        else:
            try:
                description = utils.get_age_bracket(dob=dob)
                print 'Age bracket:', description
            except Exception as e:
                print ' >> ERROR -', e

    elif args.command == 'get-postcode-point':
        postcode = ' '.join(args.arguments)
        print 'Postcode:', postcode
        if not postcode:
            print ' >> ERROR - Missing postcode argument'
            print
            parser.print_help()
        else:
            try:
                point = utils.get_postcode_point(postcode=postcode)
                print 'Point:', point
            except Exception as e:
                print ' >> ERROR -', e

    elif args.command == 'get-postcodes-distance':
        try:
            postcode_from = args.arguments[0]
            postcode_to = args.arguments[1]
        except IndexError:
            print ' >> ERROR - 2 postcodes required'
            print
            parser.print_help()
        else:
            try:
                distance = utils.get_postcodes_distance(postcode_from=postcode_from, postcode_to=postcode_to)
                print 'Distance (km, miles):', distance
            except Exception as e:
                print ' >> ERROR -', e

    elif args.command == 'extract-tags':
        try:
            tagstring = args.arguments[0]
        except IndexError:
            tagstring = None
        if not tagstring:
            print ' >> ERROR - Missing tags argument (string)'
            print
            parser.print_help()
        else:
            print 'String:', tagstring
            try:
                tags = utils.Extractor(tagstring).extract_tags()
                print 'Tags:', tags
            except Exception as e:
                print ' >> ERROR -', e

    elif args.command == 'extract-flags':
        try:
            flagstring = args.arguments[0]
        except IndexError:
            flagstring = None
        if not flagstring:
            print ' >> ERROR - Missing flags argument (string)'
            print
            parser.print_help()
        else:
            print 'String:', flagstring
            try:
                flags = utils.Extractor(flagstring).extract_flags()
                print 'Flags:', flags
            except Exception as e:
                print ' >> ERROR -', e

    else:
        parser.print_help()
