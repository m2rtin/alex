#!/usr/bin/env python
# -*- coding: utf-8 -*-
import autopath

import argparse

from alex.components.hub import Hub
from alex.components.slu.da import DialogueAct, DialogueActNBList, \
    DialogueActException, DialogueActItemException
from alex.components.dm.common import dm_factory, get_dm_type
from alex.utils.config import Config
from alex.utils.exception import SemHubException

class SemHub(Hub):
    """
      SemHub builds a text based testing environment for the dialogue manager components.

      It reads dialogue acts from the standard input and passes it to the selected dialogue manager.
      The output is the form dialogue acts.
    """
    hub_type = "SHub"

    def __init__(self, cfg):
        super(SemHub, self).__init__(cfg)

        dm_type = get_dm_type(cfg)
        self.dm = dm_factory(dm_type, cfg)
        self.dm.new_dialogue()

    def parse_input_da(self, l):
        """Converts a text including a dialogue act and its probability into a dialogue act instance and float probability.

        The input text must have the following form:
            [prob] the dialogue act

        """
        ri = l.find(" ")

        prob = 1.0

        if ri != -1:
            da = l[ri + 1:]

            try:
                prob = float(l[:ri])
            except:
                # I cannot convert the first part of the input as a float
                # Therefore, assume that all the input is a DA
                da = l
        else:
            da = l

        try:
            da = DialogueAct(da)
        except (DialogueActException, DialogueActItemException):
            raise SemHubException("Invalid dialogue act: s")

        return prob, da

    def output_da(self, da):
        """Prints the system dialogue act to the output."""
        print "System DA:", unicode(da)
        print

    def input_da_nblist(self):
        """Reads an N-best list of dialogue acts from the input. """

        self.init_readline()

        nblist = DialogueActNBList()
        i = 1
        while i < 100:
            l = raw_input("User DA %d: " % i)
            if len(l) == 1 and l.startswith("."):
                print
                break

            try:
                prob, da = self.parse_input_da(l)
            except SemHubException as e:
                print e
                continue

            nblist.add(prob, da)

            i += 1

        nblist.merge()
        nblist.scale()
        nblist.add_other()
        
        return nblist

    def run(self):
        """Controls the dialogue manager."""

        self.cfg['Logging']['system_logger'].info("""Enter the first user dialogue act. You can enter multiple dialogue acts to create an N-best list.
        The probability for each dialogue act must be be provided before the the dialogue act itself.
        When finished, the entry can be terminated by a period ".".

        For example:

          System DA 1: 0.6 hello()
          System DA 2: 0.4 hello()&inform(type="bar")
          System DA 3: .
        """)

        while True:
            sys_da = self.dm.da_out()
            self.output_da(sys_da)

            nblist = self.input_da_nblist()
            self.dm.da_in(nblist)

        print nblist

#########################################################################
#########################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
        SemHub is a text based testing environment for the dialogue manager components.

        It reads dialogue acts from the standard input and passes it to the selected dialogue manager.
        The output is the form dialogue acts.

        The program reads the default config in the resources directory ('../resources/default.cfg') config
        in the current directory.

        In addition, it reads all config file passed as an argument of a '-c'.
        The additional config files overwrites any default or previous values.

      """)

    parser.add_argument(
        '-c', action="store", dest="configs", default=None, nargs='+',
        help='additional configure file')
    args = parser.parse_args()

    cfg = Config('../resources/default.cfg')

    if args.configs:
        for c in args.configs:
            cfg.merge(c)
    cfg['Logging']['system_logger'].info('config = ' + str(cfg))

    #########################################################################
    #########################################################################
    cfg['Logging']['system_logger'].info("Sem Hub\n" + "=" * 120)

    shub = SemHub(cfg)

    shub.run()