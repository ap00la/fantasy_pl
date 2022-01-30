import time
import pandas as pd

def timer(f):
    def wrapper(*args, **kwargs):
        t_start = time.time()
        result = f(*args, **kwargs)
        t_end = time.time()
        if f.__name__ == 'wrapper':
            # do this
            print(f'Function took {1000*(t_end - t_start):.5f}ms to compute.')
            return result
        print(f'{f.__name__} took {1000*(t_end - t_start):.5f}ms to compute.')
        return result
    return wrapper


def multidf(f):
    '''
    Multiframe looper.

    Requires the multiframe object to be the first object called within the function.
    '''
    def wrapper(data, *args, **kwargs):
        if isinstance(data, pd.DataFrame):
            print(f'Single DataFrame for {f.__name__}')
            return f(data, *args, **kwargs)

        elif isinstance(data, tuple or list):
            print(f'Multiple DataFrame method for {f.__name__}')
            return tuple(f(i, *args, **kwargs,) for i in data)
        
        else:
            raise TypeError('Invalid input for get_length()')
    
    return wrapper
    
