
from pprint import pprint
import struct
import json
from pptree import *
data = json.load(open('simple_router.json'))
commands=[]
file = open("commands.txt")
for eachline in file.readlines():
	commands.append(eachline.strip('\n').split(' '))

DFS_stack=[]
class Tree(object):
    def __init__(self,l,r,d,c):
        self.left = l
        self.right = r
        self.name=d;
        self.condition = c
        self.action=None;
        self.changedfields=None;
        self.fun_name=None;
        self.args=None;

def printStats(root):
	paths=list(dfsallpaths(root,"_drop"))
	conditions=list(dfsallconditions(root,"_drop"))
	# print conditions
	
	for i, condition in enumerate(conditions, start=0):
		allcondition=""
		# print i;
		for nodes in condition:
			# print nodes
			if(not(nodes == "" or nodes == None)):
				allcondition+="^(" + nodes +")"
		conditions[i]=allcondition[1:]


	# pprint (conditions)

	for i, condition in enumerate(conditions, start=0):
		print "\n\n***************path number: ", i, "***************"	
		for nodes2 in paths[i]:
			print nodes2.name
		print "\nCondition is:"	
		print condition

def DFS(root):
	global DFS_stack
	DFS_stack.append(root)
	visited=[]
	while len(DFS_stack)>0:
		curr_node=DFS_stack.pop();
		if(curr_node not in visited):
			visited.append(curr_node)
			if(curr_node.right):
				DFS_stack.insert(0,curr_node.right)
			if(curr_node.left):	
				DFS_stack.insert(0,curr_node.left)
	return visited	

def dfsallconditions(root,dst): #root is node, dst is name of function
	stack=[(root,[root])]
	conditions=[(root.condition,[root.condition])]
	# print "here",stack
	condition=""
	while stack:
		(vertex, path)=stack.pop()
		(condition_pop1,condition_pop)=conditions.pop()
		nextvertexlist=[]
		if(vertex.right):
			nextvertexlist.append(vertex.right)
		if(vertex.left):
			nextvertexlist.append(vertex.left)
			
		for i, nextvertex in enumerate(nextvertexlist, start=0):
			if(i == 0):
				if(nextvertex.condition):
					condition=nextvertex.condition
				else:
					condition=""	
			else:
				if nextvertex.condition:
					condition="!("+nextvertex.condition+")"	
				else:
					condition=""	
			# condition=condition.encode('ascii','ignore');
			if(nextvertex.name == dst):
				# yield path+[nextvertex]
				yield condition_pop+[condition]
			else:
				conditions.append((condition, condition_pop+[condition]))	
				stack.append((nextvertex, path + [nextvertex]))
		# print "hereee2", stack

def dfsallpaths(root,dst): #root is node, dst is name of function
	stack=[(root,[root])]
	while stack:
		(vertex, path)=stack.pop()
		nextvertexlist=[]
		if(vertex.right):
			nextvertexlist.append(vertex.right)
		if(vertex.left):
			nextvertexlist.append(vertex.left)
			
		for i, nextvertex in enumerate(nextvertexlist, start=0):
			if(nextvertex.name == dst):
				yield path+[nextvertex]
			else:
				stack.append((nextvertex, path + [nextvertex]))					 		

def inorder(root):
	if root ==None:
		return
	else:
		inorder(root.left)
		print(root.name,root.condition)	
		inorder(root.right)

def search(paser_states,node):

	for i, state in enumerate(parser_states, start=0):
		if(state["name"]  == node.name):
			if not state["transition_key"]:
				next_state=state["transitions"][0]["next_state"]

				return Tree(None,None,next_state,None)
				
			else:

				next_state=state["transitions"][0]["next_state"]
				cond=""
				for i in state["transition_key"][0]["value"]:
					cond+=i+"."
				cond+="=="+str(state["transitions"][0]["value"]);
				node.condition=cond
				return Tree(None, None,next_state,cond)
			break;				


def formulate_parser_tree(liststate, node):
	if not liststate or node is None: 
		return
	else:
		right=search(liststate,node)
		node.right=right;

		if(right is not None):
			for i, state in enumerate(parser_states, start=0):
				if(state["name"]  == right.name):
					del liststate[i]

		return formulate_parser_tree(liststate,right)

def formulate_exp(dic):
	try:
		if(dic == None):
			return " ";
	except KeyError:
		pass;

	if(dic["type"] != "expression"):
		return dic["value"]
	else:
		return str(formulate_exp(dic["value"]["left"]))+str(dic["value"]["op"])+str(formulate_exp(dic["value"]["right"]))


def search_next_control_node(ingress_tables,node):
	for i, table in enumerate(ingress_tables, start=0):
		if (table["name"] == node.name):
			condition=""
			for j in table["key"][0]["target"]:
				condition+=j+"."

			for j in commands:
				if(j[1] == node.name and j[0] == 'table_add'):
					condition+="=="+j[3]
					arg_list=commands[5:]
			true_state  = table["actions"][1]
			false_state = table["actions"][0]
			node.condition=condition
			right=Tree(None, None, true_state,None)		
			node.right=right
			left=Tree(None,None,false_state,None)
			node.left=left
			right.action=True
			left.action=True;
			fill_action_states(right,arg_list)
			return node,node.right,node.left

def fill_action_states(node,arg_list):
	fun_name=[]
	for i in data['actions']:
		if( i["name"] == node.name):
			for j in range(len(i['runtime_data'])):
				i[j]=arg_list[j]
				for k in i["primitives"]:
					fun_name.append(k)
			node.fun_name=fun_name;
			node.args=arg_list

def formulate_control_graph(ingress_tables,node,stringname):
	if not ingress_tables or node is None:
		return
	else:
		if(node.action):
			for i, table in enumerate(ingress_tables, start=0):
				if node.name in table["actions"]:
					next_true_state=table["next_tables"][node.name]
					right=Tree(None,None,next_true_state,None);
					node.right=right;
					left=None;		
					del ingress_tables[i]
					break;
		else:
			node,right,left=search_next_control_node(ingress_tables,node)
		formulate_control_graph(ingress_tables,right,"right");
		formulate_control_graph(ingress_tables,left,"left");

		


parser_states=[]
start = data["parsers"][0]
init_parser=data["parsers"][0]["init_state"]
start = data["parsers"][0]["parse_states"]
length = len(start)
for i in start:
	parser_states.append(i);


for i, state in enumerate(parser_states, start=0):
	if(state["name"]  == init_parser):
		if not state["transition_key"]:
			next_state=state["transitions"][0]["next_state"]
			root=Tree(None,None,init_parser,None)
		else:
			next_state=state["transitions"][0]["next_state"]
			cond=""
			for i in state["transition_key"]["value"]:
				cond+=i+"."
			cond+="=="+str(state["transitions"]["value"]);
			root=Tree(None, None,init_parser,cond,"")		
		right=search(parser_states,root)
		root.right=right		
		break;		
del parser_states[i]
tree = formulate_parser_tree(parser_states,root.right)

print("---------------Parser-------------")
inorder(root);	

ParserNodesList=DFS(root);
print ParserNodesList;



control = data["pipelines"]
ingress=control[0]

ingress_tables=ingress["tables"]

init_table=str(ingress["init_table"])



for key in ingress:
	if(key == "conditionals" and isinstance(ingress[key],list) and len(ingress[key])):
		listObjects=ingress[key]
		for j in listObjects:
			if(j["name"] == init_table):
				
				condition=formulate_exp(j["expression"])
true_state=ingress["conditionals"][0]["true_next"]
false_state=ingress["conditionals"][0]["false_next"]




control_root=Tree(None,None,"ingress",0) 
control_conditional=Tree(None,None,"conditionals",condition) 
control_root.right=control_conditional;
conditional_true_state=Tree(None, None,true_state,None)
conditional_false_state=Tree(None, None,false_state,None)
control_conditional.right=conditional_true_state
control_conditional.left=conditional_false_state			

conditional_true_state,right,left=search_next_control_node(ingress_tables,conditional_true_state)
formulate_control_graph(ingress_tables,control_conditional.right,"rootright");

print("---------------Ingress-------------")
inorder(control_conditional);


ParserNodesList[-1].right=control_root;



# egress
egress=control[1]
init_egress_table=str(egress["init_table"])
egress_tables=egress["tables"]
if(len(egress["conditionals"]) and egress["conditionals"][0]["name"]  == init_egress_table):
	for key in egress:
		if(key == "conditionals" and isinstance(egress[key],list) and len(egress[key])):
			listObjects=egress[key]
			for j in listObjects:
				if(j["name"] == init_egress_table):
					
					condition=formulate_exp(j["expression"])
					pprint(condition)
	true_state=egress["conditionals"][0]["true_next"]
	false_state=egress["conditionals"][0]["false_next"]




	control_root=Tree(None,None,"egress",0) 
	control_conditional=Tree(None,None,"conditionals",condition) 
	root.right=control_conditional;
	conditional_true_state=Tree(None, None,true_state,None)
	conditional_false_state=Tree(None, None,false_state,None)
	control_conditional.right=conditional_true_state
	control_conditional.left=conditional_false_state			

	conditional_true_state,right,left=search_next_control_node(ingress_tables,conditional_true_state)
	formulate_control_graph(ingress_tables,control_conditional.right,"rootrifgt");

else:
	for i, state in enumerate(egress_tables, start=0):
		if(state["name"] == init_egress_table):
			root_egress=Tree(None,None,init_egress_table,None)
			break;
	formulate_control_graph(egress_tables,root_egress,"root")
	node=root_egress	

print("---------------Egress-------------")
inorder(root_egress)

#deparser

deparser=data["deparsers"][0]
order_of_header=[]
for i in deparser["order"]:
	order_of_header.append(i);

print("---------------Deparser-------------")
print order_of_header		



printStats(root);




