# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
from parlai.core.params import ParlaiParser
from parlai.mturk.tasks.model_evaluator.worlds import ModelEvaluatorWorld
from parlai.mturk.core.agents import MTurkAgent, MTurkManager
from task_config import task_config
import time
import os
import copy
try:
    from joblib import Parallel, delayed
except ModuleNotFoundError:
    raise SystemExit("Please install joblib by running: pip install joblib")


def main():
    argparser = ParlaiParser(False, False)
    argparser.add_parlai_data_path()
    argparser.add_mturk_args()

    # The dialog model we want to evaluate
    from parlai.agents.ir_baseline.ir_baseline import IrBaselineAgent
    IrBaselineAgent.add_cmdline_args(argparser)
    opt = argparser.parse_args()
    opt['task'] = os.path.basename(os.getcwd())
    opt.update(task_config)

    # The task that we will evaluate the dialog model on
    task_opt = {}
    task_opt['datatype'] = 'test'
    task_opt['datapath'] = opt['datapath']
    task_opt['task'] = '#MovieDD-Reddit'
    
    global run_hit
    def run_hit(i, opt, task_opt, mturk_manager):
        model_agent = IrBaselineAgent(opt=opt)
        # Create the MTurk agent which provides a chat interface to the Turker
        mturk_agent = MTurkAgent(id='Worker', manager=mturk_manager, conversation_id=i, opt=opt)
        world = ModelEvaluatorWorld(opt=opt, model_agent=model_agent, task_opt=task_opt, mturk_agent=mturk_agent)
        while not world.episode_done():
            world.parley()
        world.shutdown()

    mturk_manager = MTurkManager()
    mturk_manager.init_aws(opt=opt)
    results = Parallel(n_jobs=opt['num_hits'], backend='threading')(delayed(run_hit)(i, opt, task_opt, mturk_manager) for i in range(1, opt['num_hits']+1))
    mturk_manager.review_hits()
    mturk_manager.shutdown()

if __name__ == '__main__':
    main()
