import math
import numpy as np
import pandas as pd

class DataLoader():
    """A class for loading and transforming data for the lstm model"""

    def __init__(self, filename, split, cols, cols_to_norm, pred_len):
        dataframe = pd.read_csv(filename)
        i_split = int(len(dataframe) * split)
        self.data_train = dataframe.get(cols).values[:i_split]
        # print(self.data_train[:10])
        self.data_test  = dataframe.get(cols).values[i_split:]
        # print(len(self.data_test))
        # print(self.data_test)
        self.cols_to_norm = cols_to_norm
        self.pred_len = pred_len
        self.len_train  = len(self.data_train)
        self.len_test   = len(self.data_test)
        self.len_train_windows = None

    def get_test_data(self, seq_len, normalise, cols_to_norm):
        '''
        Create x, y test data windows
        Warning: batch method, not generative, make sure you have enough memory to
        load data, otherwise reduce size of the training split.
        '''
        data_windows = []
        for i in range(self.len_test - seq_len):
            data_windows.append(self.data_test[i:i+seq_len])

        data_windows = np.array(data_windows).astype(float)
        y_base = data_windows[:, 0, [0]]
        # data_windows = self.normalise_windows(data_windows, single_window=False) if normalise else data_windows
        data_windows = self.normalise_selected_columns(data_windows, cols_to_norm, single_window=False) if normalise else data_windows
        cut_point = self.pred_len
        # x = data_windows[:, :-cut_point:]
        x = data_windows[:, :-1, :]
        y = data_windows[:, -1, [0]]
        return x,y,y_base

    def get_train_data(self, seq_len, normalise):
        '''
        Create x, y train data windows
        Warning: batch method, not generative, make sure you have enough memory to
        load data, otherwise use generate_training_window() method.
        '''
        data_x = []
        data_y = []
        for i in range(self.len_train - seq_len):
            x, y = self._next_window(i, seq_len, normalise)
            data_x.append(x)
            data_y.append(y)
        return np.array(data_x), np.array(data_y)

    def generate_train_batch(self, seq_len, batch_size, normalise):
        '''Yield a generator of training data from filename on given list of cols split for train/test'''
        i = 0
        while i < (self.len_train - seq_len):
            x_batch = []
            y_batch = []
            for b in range(batch_size):
                if i >= (self.len_train - seq_len):
                    # stop-condition for a smaller final batch if data doesn't divide evenly
                    yield np.array(x_batch), np.array(y_batch)
                    i = 0
                x, y = self._next_window(i, seq_len, normalise)
                x_batch.append(x)
                y_batch.append(y)
                i += 1
            yield np.array(x_batch), np.array(y_batch)

    def _next_window(self, i, seq_len,normalise):
        '''Generates the next data window from the given index location i'''
        window = self.data_train[i:i+seq_len]
        # window = self.normalise_windows(window, single_window=True)[0] if normalise else window
        window = self.normalise_selected_columns(window, self.cols_to_norm, single_window=True)[0] if normalise else window       
        # x = window[:-1]
        x = window[:-1]
        # y = window[0][2][0]
        y = window[-1, [0]]
        return x, y
 
    def normalise_windows(self, window_data, single_window=False):
        '''Normalise window with a base value of zero'''
        normalised_data = []
        window_data = [window_data] if single_window else window_data
        for window in window_data:
            normalised_window = []
            for col_i in range(window.shape[1]):
                w = window[0, col_i]
                if w == 0:
                  w = 1
                normalised_col = [((float(p) / float(w)) - 1) for p in window[:, col_i]]
                normalised_window.append(normalised_col)
            normalised_window = np.array(normalised_window).T # reshape and transpose array back into original multidimensional format
            normalised_data.append(normalised_window)
        return np.array(normalised_data)

    # Modified normalization function to normalize only specific columns
    def normalise_selected_columns(self, window_data, columns_to_normalise, single_window=False):
        normalised_data = []
        window_data = [window_data] if single_window else window_data
        for window in window_data:
            normalised_window = []
            for col_i in range(window.shape[1]):
                if col_i in columns_to_normalise:
                    # Normalize only if the column index is in the list of columns to normalize
                    w = window[0, col_i]
                    if w == 0:
                        w = 1
                    normalised_col = [((float(p) / float(w)) - 1) for p in window[:, col_i]]
                else:
                    # Keep the original data for columns not in the list
                    normalised_col = window[:, col_i].tolist()
                normalised_window.append(normalised_col)
            normalised_window = np.array(normalised_window).T
            normalised_data.append(normalised_window)
        return np.array(normalised_data)
