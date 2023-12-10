import time 

def decorator(f):
    def new_function():
        print("Extra Functionality")
        f()
    return new_function

@decorator
def initial_function():
    print("Initial Functionality")

initial_function()
initial_function()

# if __name__ == "__main__":
#     frame_time = .25

#     while True:
#         obj = object()
#         obj.foo()
#         # start = time.time()
#         # print(f"start: {start}")
#         # time.sleep(.01)
#         # end = time.time()
#         # print(f"end:{end}")
#         # delta = end - start
#         # sleep_time = frame_time - delta
#         # print(f"delta:{delta}")
#         # print(f"sleep:{sleep_time}")
#         # if sleep_time > 0:
#         #     time.sleep(frame_time - delta)


