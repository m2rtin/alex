#!/usr/bin/env python
# -*- coding: utf-8 -*-
import autopath

import multiprocessing
import sys
import time
import argparse

import alex.utils.audio as audio
import alex.utils.various as various
from alex.components.hub.aio import AudioIO
from alex.components.hub.messages import Command, Frame
from alex.utils.config import Config

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
        test_vio.py tests the VoipIO component.

        The program reads the default config in the resources directory
        ('../resources/default.cfg') and any additional config files passed as
        an argument of a '-c'. The additional config file overwrites any
        default or previous values.

      """)

    parser.add_argument(
        '-c', action="store", dest="configs", default=None, nargs='+',
        help='additional configuration file')
    args = parser.parse_args()

    cfg = Config('../resources/default.cfg')
    if args.configs:
        for c in args.configs:
            cfg.merge(c)

    session_logger = cfg['Logging']['session_logger']
    system_logger = cfg['Logging']['system_logger']
    system_logger.info('config = {cfg!s}'.format(cfg=cfg))

    #########################################################################
    #########################################################################
    system_logger.info("Test of the AudioIO component\n" + "=" * 120)

    wav = audio.load_wav(cfg, './resources/test16k-mono.wav')
    # split audio into frames
    wav = various.split_to_bins(wav, 2 * cfg['Audio']['samples_per_frame'])
    # remove the last frame

    aio_commands, aio_child_commands = multiprocessing.Pipe()  # used to send aio_commands
    audio_record, child_audio_record = multiprocessing.Pipe()  # I read from this connection recorded audio
    audio_play, child_audio_play = multiprocessing.Pipe()      # I write in audio to be played

    aio = AudioIO(cfg, aio_child_commands, child_audio_record, child_audio_play)

    aio.start()

    count = 0
    max_count = 2500
    while count < max_count:
        time.sleep(cfg['Hub']['main_loop_sleep_time'])
        count += 1

        # write one frame into the audio output
        if wav:
            data_play = wav.pop(0)
            #print len(wav), len(data_play)
            audio_play.send(Frame(data_play))

        # read all recorded audio
        if audio_record.poll():
            data_rec = audio_record.recv()

    aio_commands.send(Command('stop()'))
    aio.join()

    print()