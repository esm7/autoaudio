#!/usr/bin/python3
import argparse
import os
import sys
import pulsectl
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--load-profile', help="Load a profile stored in the config file by name")
parser.add_argument('--capture', action='store_true',
                    help="Capture the current PulseAudio state (chosen output, profile, sink) so "
                         "it can easily be copied to a configuration")
args = parser.parse_args()

config_file_path = os.path.join(os.environ['HOME'], '.config', 'autoaudio.yaml')

if not os.path.exists(config_file_path):
    print("Error, can't find config file")
    sys.exit(1)

config = yaml.full_load(open(config_file_path))


def do_profile_rule(rule_name, config_rule, pulse):
    print(f"Testing rule '{rule_name}'...")
    rule_succeeded = True
    failure_reason = ''
    for command in config_rule:
        name, args = list(command.items())[0]
        if name == 'if_have_card':
            card_names = [card.name for card in pulse.card_list()]
            if args not in card_names:
                rule_succeeded = False
                failure_reason = f"Card {args} not found"
                break
            print(f"  Found card {args} required by rule {rule_name}")
        elif name == 'set_profile':
            card_name = args['card']
            profile_name = args['profile']
            print(f"  Trying to set card {card_name} to profile {profile_name}")
            card = pulse.get_card_by_name(card_name)
            try:
                pulse.card_profile_set(card, profile_name)
            except pulsectl.PulseIndexError:
                print("  Can't set profile")
                rule_succeeded = False
                failure_reason = f"Card {card_name} can't be set to profile {profile_name}"
                break
        elif name == 'set_default_sink':
            print(f"  Trying to set the default sink to {args}")
            try:
                sink = pulse.get_sink_by_name(args)
                pulse.sink_default_set(sink)
            except pulsectl.PulseIndexError:
                print("  Can't find or set the sink")
                rule_succeeded = False
                break
        elif name == 'set_default_source':
            print(f"  Trying to set the default source to {args}")
            try:
                source = pulse.get_source_by_name(args)
                pulse.source_default_set(source)
            except pulsectl.PulseIndexError:
                print("  Can't find or set the source")
                rule_succeeded = False
                break
        elif name == 'exec':
            print(f"  Executing command '{args}'")
            retval = os.system(args)
            if retval != 0:
                print(f"  Command returned error code {retval}, failing the rule")
                rule_succeeded = False
                break
        else:
            print(f"  Error, unknown command name '{name}', failing the rule")
            rule_succeeded = False
            break
    if rule_succeeded:
        print(f"Rule '{rule_name}' succeeded!")
    return rule_succeeded, failure_reason


def get_card_by_index(pulse, card_index):
    return next((card for card in pulse.card_list() if card.index == card_index), None)


def capture_current_config(pulse):
    default_sink = pulse.get_sink_by_name(pulse.server_info().default_sink_name)
    default_source = pulse.get_source_by_name(pulse.server_info().default_source_name)
    sink_card = get_card_by_index(pulse, default_sink.card)
    source_card = get_card_by_index(pulse, default_source.card)
    config = {
        'profile_name': [
            {'rule_name': [
                {'if_have_card': sink_card.name},
                {'set_profile': {
                    'card': sink_card.name,
                    'profile': sink_card.profile_active.name
                }},
                {'set_default_sink': default_sink.name}
            ]}
        ]
    }
    if sink_card.name == source_card.name:
        print("Including the default source in the capture")
        config['profile_name'][0]['rule_name'].append({'set_default_source': default_source.name})
    else:
        print(f"Note: the default source ('{default_source.name}') is not included in the capture because it seems to belong to "
              "a different card than your default sink's card.")
    print(yaml.dump(config))


def notify(rule_succeeded, failure_reason, rule_name, rule_config, profile_name):
    if config.get('general'):
        notifier = config['general'].get('notifier')
        if notifier is not None:
            if rule_succeeded:
                message = f"Audio profile rule '{rule_name}' succeeded"
            else:
                message = f"Could not match any rule in profile '{profile_name}'"
            os.system(f"{notifier} -u {'low' if rule_succeeded else 'critical'} "
                      f'AutoAudio "{message}"')


with pulsectl.Pulse('autoaudio') as pulse:
    if args.load_profile is not None:
        print(f"Loading profile {args.load_profile}")
        if config.get('profiles') is not None and args.load_profile in config.get('profiles'):
            profile_config = config['profiles'][args.load_profile]
            for rule in profile_config:
                if len(rule) != 1:
                    print("Rules are expected to have just 1 dict element:", profile_config)
                    sys.exit(1)
                rule_name, rule_config = list(rule.items())[0]
                rule_succeeded, failure_reason = do_profile_rule(rule_name, rule_config, pulse)
                if rule_succeeded:
                    print("Seems like we're done :)")
                    break
            notify(rule_succeeded, failure_reason, rule_name, rule_config, args.load_profile)
        else:
            print(f"Profile {args.load_profile} can't be found in the configuration file.")
            if config.get('profiles') is not None:
                print("Available profiles:", config['profiles'].keys())
    elif args.capture:
        capture_current_config(pulse)
    else:
        print("Not asked to load a profile, so I'm just dumping lots of information...")
        print("Sinks:")
        for sink in pulse.sink_list():
            print(sink)
        print("Sources:")
        for source in pulse.source_list():
            print(source)
        print("Cards:")
        for card in pulse.card_list():
            print(card)
            print("  Active profile:", card.profile_active.name)
            for profile in card.profile_list:
                print("  Profile:", profile)
        default_sink = pulse.server_info().default_sink_name
        default_source = pulse.server_info().default_source_name
        print("Current default sink:", default_sink)
        print("Current default source:", default_source)
        print("Available profiles in autoaudio.yaml:", list(config['profiles'].keys()) if 'profiles' in config else 'None')

