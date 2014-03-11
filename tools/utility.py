#!/usr/bin/env python
import argparse
import os
import sys

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    if not BASE_DIR:
        APP_ROOT = os.path.abspath('..')
        sys.path.append(APP_ROOT)
    else:
        sys.path.append(os.path.abspath(BASE_DIR))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings'

    from mumlife import utils

    choices = [
        'get-age',                  # Get age
        'get-age-bracket',          # Get age bracket from DoB
        'get-postcode-point',       # Get location point for postcode
        'get-postcodes-distance',   # Get distance between 2 postcodes
        'parse-text',               # Parse and format hashtags, flags and links
        'extract-tags',             # Extract tag from string
        'extract-flags',            # Extract flags from string
        'get-messages',             # List messages for given member
        'get-events',               # List events for given member
        'get-notifications',        # List notifications for given member
    ]
    parser = argparse.ArgumentParser(description="Mumlife Command-Line Test Tool")
    parser.add_argument('command', type=str, help='command to execute', choices=choices)
    parser.add_argument('arguments', type=str, nargs='*', help='command arguments')
    args = parser.parse_args()

    if args.command == 'get-age':
        try:
            dob = args.arguments[0]
        except IndexError:
            print ' >> ERROR - date of birth required; format: YYYY-MM-DD (e.g. 1978-11-24)'
            print
            parser.print_help()
        else:
            try:
                age = utils.get_age(born=dob)
                print 'Age :', age
            except Exception as e:
                print ' >> ERROR -', e

    elif args.command == 'get-age-bracket':
        try:
            dob = args.arguments[0]
        except IndexError:
            print ' >> ERROR - date of birth required; format: YYYY-MM-DD (e.g. 1978-11-24)'
            print
            parser.print_help()
        else:
            try:
                description = utils.get_age_bracket(born=dob)
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

    elif args.command == 'parse-text':
        try:
            text = args.arguments[0]
        except IndexError:
            text = None
        if not text:
            print ' >> ERROR - Missing text (string)'
            print
            parser.print_help()
        else:
            print 'Parsing:'
            print '-------'
            print text
            try:
                parsed_text = utils.Extractor(text).parse()
                print '>'
                print parsed_text
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

    elif args.command == 'get-messages':
        try:
            user_id = args.arguments.pop(0)
        except IndexError:
            print ' >> ERROR - Missing Member ID'
            print
            parser.print_help()
        else:
            from mumlife.models import Member
            member = Member.objects.get(pk=int(user_id))
            arguments = dict([(a[0], a[1]) for a in [arg.split('=') for arg in args.arguments]])
            messages = member.get_messages(**arguments)
            if messages.count():
                for m in messages:
                    print '>', repr(m)
            else:
                print '>> No Messages found.'

    elif args.command == 'get-events':
        try:
            user_id = args.arguments.pop(0)
        except IndexError:
            print ' >> ERROR - Missing Member ID'
            print
            parser.print_help()
        else:
            from mumlife.models import Member
            member = Member.objects.get(pk=int(user_id))
            arguments = dict([(a[0], a[1]) for a in [arg.split('=') for arg in args.arguments]])
            events = member.get_events(**arguments)
            if len(events):
                for ev in events:
                    print '>', repr(ev)
            else:
                print '>> No Events found.'

    elif args.command == 'get-notifications':
        try:
            user_id = args.arguments.pop(0)
        except IndexError:
            print ' >> ERROR - Missing Member ID'
            print
            parser.print_help()
        else:
            from mumlife.models import Member
            member = Member.objects.get(pk=int(user_id))
            notifications = member.get_notifications()
            for n in notifications:
                print '>', repr(n)

    else:
        parser.print_help()
