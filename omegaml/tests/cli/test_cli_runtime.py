import os
import sys
from unittest import TestCase

import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

from omegaml import Omega
from omegaml.tests.cli.scenarios import CliTestScenarios
from omegaml.tests.util import OmegaTestMixin


class CliRuntimeTests(CliTestScenarios, OmegaTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.om = Omega()
        self.clean()

    def test_cli_runtime_model_fit_predict(self):
        self.make_model('reg')
        reg = self.om.models.get('reg')
        self.make_dataset_from_dataframe('test', N=10)
        # -- fit the model
        self.cli('runtime model reg fit test[x] test[y]')
        self.assertLogContains('info', 'Metadata')
        # -- run a prediction, we get back actual data
        self.cli('runtime model reg predict test[x]', new_start=True)
        self.assertLogContains('info', '[[')
        self.assertIsInstance(self.get_log('info')[0][0], np.ndarray)
        # -- run a prediction, we store the results
        self.cli('runtime model reg predict test[x] --result predictions')
        #    expect metadata since we ask to write data to predictions
        self.assertLogContains('info', 'Metadata')
        df_expect = self.om.datasets.get('test')['y']
        #    check the data has actually been stored as requested
        df_pred = self.om.datasets.get('predictions')
        self.assertIsNotNone(df_pred)
        self.assertEqual(len(df_expect), len(df_pred))

    def test_cli_runtime_model_gridsearch(self):
        X, y = make_classification()
        logreg = LogisticRegression(solver='liblinear')
        self.om.models.put(logreg, 'logreg')
        # perform gridsearch on runtime
        self.om.datasets.put(X, 'testX')
        self.om.datasets.put(y, 'testY')
        self.cli('runtime model logreg gridsearch testX testY --param C=[.1,.5,1.0]')
        model_meta = self.om.models.metadata('logreg')
        self.assertIn('gridsearch', model_meta.attributes)
        gsmodel_name = model_meta.attributes['gridsearch'][0]['gsModel']
        gsmodel = self.om.models.get(gsmodel_name)
        self.assertIsInstance(gsmodel, GridSearchCV)

    def test_cli_runtime_script_run(self):
        pkgpath = self.get_package_path()
        self.cli(f'scripts put {pkgpath} helloworld')
        self.assertLogContains('info', 'Metadata')
        # run without kwargs
        self.cli('runtime script helloworld run', new_start=True)
        self.assertLogContains('info', 'hello from helloworld')
        # with kwargs
        self.cli('runtime script helloworld run foo=bar', new_start=True)
        self.assertLogContains('info', '"foo": "bar"')


