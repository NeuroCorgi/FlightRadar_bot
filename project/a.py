import numpy as np

a = np.array([[0, 1, 0, 1],
              [1, 1, 0, 0],
              [0, 0, 1, 0]])
b = np.array([[1, 2, 1]])
print(b)
print(b.T)

print(np.concatenate((a, b.T), axis=1))