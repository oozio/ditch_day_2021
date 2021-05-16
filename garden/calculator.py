def grow(prev_size):
  return (100-prev_size)//3 + prev_size

def shrink(prev_size):
  return prev_size//2 + 2
