import unittest

from qiskit_machine_learning.datasets import ad_hoc_data


class Test(unittest.TestCase):
    def test_b2(self):
        feature_dim = 2
        training_dataset_size = 20
        testing_dataset_size = 10

        sample_Total, training_input, test_input, class_labels = ad_hoc_data(training_size=training_dataset_size,
                                                                       test_size=testing_dataset_size,
                                                                       gap=0.3,
                                                                       n=feature_dim,
                                                                       plot_data=True)

        # Siguiente paso del issue: split_dataset_to_data_and_labels(test_input)
        # (qiskit-aqua) trata test_input como un dict {clase: muestras}.
        sorted_classes_name = sorted(list(test_input.keys()))
        n_test = sum(len(test_input[k]) for k in sorted_classes_name)

        self.assertEqual(n_test, 2 * testing_dataset_size)


if __name__ == '__main__':
    unittest.main(argv=[''])
