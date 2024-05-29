from ..lslHandler import lslHandler


# NOTE: usually it is forbidden to use global variables with Dash, 
# but due to the simple fact that dcc.storage is way too slow we will use it anyways
# the requirements for it to work is that dash is run with only 1 woker and 1 user at a time

lsl_handler = lslHandler()

stream_to_use = None

#holds the data that the graph is displaying
graph_frame = {"time" : [], "value" : []}

#temporary
start_interval = 0

#holds the data that is fetched from the stream inbetween graph updates
buffer_frame = {"time" : [], "value" : []}