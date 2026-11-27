import unittest

from qiskit_machine_learning.datasets import ad_hoc_data


class Test(unittest.TestCase):
    def test_f2(self):
        feature_dim = 2
        training_dataset_size = 20
        testing_dataset_size = 10

        train_features, train_labels, test_features, test_labels, adhoc_total = ad_hoc_data(
            training_size=training_dataset_size,
            test_size=testing_dataset_size,
            n=feature_dim,
            gap=0.3,
            plot_data=True, one_hot=False, include_sample_total=True
        )

        n_test = len(test_features)

        self.assertEqual(n_test, 2 * testing_dataset_size)


if __name__ == '__main__':
    unittest.main(argv=[''])
