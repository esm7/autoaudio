# AutoAudio

This is a (currently) simple script that allows setting various PulseAudio configurations under Linux according to a set of rules.

Say you have a headset for music, a headset for audio calls, a headset you sometimes take with you home, a headset you use in coffee shops...
You can have AutoAudio decide automatically based on what headsets are connected, and the *profile* you want (e.g. calls or music), what
inputs and outputs should be set.

**Please note that this script is far from polished and you will very likely encounter rough edges.**

## The Basics

* A *profile* is a context for what you want to do. For example, I have a `calls` profile and a `music` profile. You typically call AutoAudio with a profile that you want to set.
* A profile comprises of *rules*. AutoAudio parses the rules one by one, item by item, until one rule fully succeeds.
* A rule is comprised of *commands*. Commands can be testing if a PulseAudio card exists, setting a PulseAudio sink (output), etc. The typical flow is for you to set a *condition command* (e.g. whether a card exists), and if it succeeds, continue to commands that set inputs, outputs etc.

## Prequisites

May be installed with `pip install -r requirements.txt`.

## Usage

1. Create a config file ~/.config/autoaudio.yaml. You may use the sample config (autoaudio.yaml.sample) as a base.
2. Change the profiles to your needs. Maybe you need just one profile, maybe more.
3. Populate cards, sinks and sources. AutoAudio can help you do this, see below.
4. Save the config and call AutoAudio (e.g. with mapped keyboard shortcuts) when you need it.

I personally have -
`autoaudio --load-profile music`
Mapped to one global system shortcut, and -
`autoaudio --load-profile calls`
mapped to another.

## Semi-Automatic Configuration

AutoAudio can try to help you with creating a configuration.
It works as follows.

1. Set up your audio setup the way you want it - i.e. set the default output, default input etc.
2. Launch `./autoaudio.py --capture`. It will output a configuration snippet that corresponds to what you currently have set.
3. Paste this snippet where you want it in `autoaudio.yaml`, being very careful about the sensitive YAML indentation.
4. Switch to other configurations (e.g. connect other headsets) and repeat the process.

## Manual Configuration

When running AutoAudio with no parameters, it dumps a list of the available PulseAudio sinks, sources, cards etc.
You can use all that data to compose the settings for `autoaudio.yaml` or debug issues with the semi-automatic configuration.

## Wishlist

1. Have a server mode that listens to PulseAudio events and runs rules automatically based on the current profile.
2. A proper installer, packaging etc.
