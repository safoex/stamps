
# coding: utf-8

# In[1]:


import gurobipy as grb
import itertools
import sys
import copy
import collections
import functools


# In[2]:


def iterer(*args):
    return itertools.product(*[x_ if isinstance(x_,collections.Iterable) else range(x_) for x_ in args])


# In[3]:


params_file = "params2.txt"
stamps = {}
prices = {}
total_price = 0
total_orgs  = 1

lines = []
def import_params():
    with open(params_file) as f:
        global lines
        lines = [ line for line in f ]
    with open("log.txt","w") as L:
        global total_price, total_orgs
        print(str(int(lines[1])), file=L)
        for l in lines[2:2+int(lines[1])]:
            nominal, amount = list(map(float, l.split()))
            stamps[nominal] = amount
        l_n_prices = 3 + int(lines[1])
        n_prices = lines[l_n_prices]
        print(n_prices, file=L)
        for p in list(map(float, lines[l_n_prices+1].split())):
            prices[p] = 0
        total_orgs = int(lines[l_n_prices+3])
        total_price = float(lines[l_n_prices+5])
        print([prices, total_orgs, total_price])

import_params()


# In[4]:


class Solver:
    # stamps - (1,N), prices - (1,N)
    def __init__(self, N_orgs, stamps, prices, total_cost):
        self.model = grb.Model("stamps")
        self.N_stamps = len(stamps)
        self.N_orgs = N_orgs
        self.N_prices = len(prices)
        self.var_stamps = self.model.addVars(range(self.N_orgs), range(self.N_stamps), name='s', vtype=grb.GRB.INTEGER)
        self.var_prices = self.model.addVars(range(self.N_orgs), range(self.N_prices), name='p', vtype=grb.GRB.INTEGER)
        self.stamps_nominal = list(stamps.keys())
        self.stamps_amount = list(stamps.values())
        self.prices = prices
        self.total_cost = total_cost
        ### contraints ###
        ### sum of stamps = price for org
        def stamp_sum_org(o):
            return grb.quicksum(self.var_stamps[o,s] * self.stamps_nominal[s] for s in range(self.N_stamps))
        def price_sum_org(o):
            return grb.quicksum(self.var_prices[o,p] * prices[p] for p in range(self.N_prices))
        self.model.addConstrs(stamp_sum_org(o) == price_sum_org(o) for o in range(self.N_orgs))
        ### at least one letter per org:
        self.model.addConstrs((self.var_prices.sum(o, '*') >= 1 for o in range(self.N_orgs)))
        ### sum of all stamps is equal to total stamps
        self.model.addConstrs(self.var_stamps.sum('*', s) == self.stamps_amount[s] for s in range(self.N_stamps))
        ### sum of all orgs = total_prices
        #self.model.addConstr()
        self.model.addConstrs(self.var_stamps[o,s] <= 20 for o,s in iterer(self.N_orgs, self.N_stamps))
        self.model.addConstrs(self.var_stamps[o,s] >= 0 for o,s in iterer(self.N_orgs, self.N_stamps))
        self.diff = (grb.quicksum(price_sum_org(o) for o in range(self.N_orgs)) -  total_cost)
        self.model.addConstr(self.diff >= 0)
        self.model.setObjective( self.diff , grb.GRB.MINIMIZE)
        
    def solve(self):
        self.model.update()
        self.model.optimize()
        return s.var_stamps, s.var_prices
    
    def print_result(self,filename):
        self.stamps = {}
        self.res_prices = {}
        self.stamps_groups = {}
        for n in self.stamps_nominal:
            self.stamps_groups[n] = {}
        
        for o,s in iterer(self.N_orgs, self.N_stamps):
            if self.var_stamps[o,s].X > 0:
                if not o in self.stamps:
                    self.stamps[o] = {}
                a = self.var_stamps[o,s].X
                n = self.stamps_nominal[s]
                if not a in self.stamps_groups[n]:
                    self.stamps_groups[n][a] = 0
                self.stamps_groups[n][a] += 1
                self.stamps[o][n] = a
                    
        for o in range(self.N_orgs):
            self.res_prices[o] = 0
        for o, p in iterer(self.N_orgs, self.N_prices):
            self.res_prices[o] += self.var_prices[o,p].X * self.prices[p]
        with open(filename, "w") as F:
            print("TOTAL MONEY %d"%(self.diff.getValue() + self.total_cost), file=F)
            print("TOTAL STAMPS %d"%(self.var_stamps.sum('*','*').getValue()), file=F)
            for o in range(self.N_orgs):
                print(o+1, file=F)
                print(self.res_prices[o], file=F)
                for s in self.stamps_nominal:
                    if s in self.stamps[o] and self.stamps[o][s] > 0:
                        print(u"%d p. by %.2f rub."%(self.stamps[o][s],s), file=F)
                print("\n", file=F)
            for n in self.stamps_nominal:
                for g in self.stamps_groups[n]:
                    total_num = g*self.stamps_groups[n][g]
                    print("%dx%.2f=%.2f"%(total_num, n, total_num*n),file=F)
            print("\n", file=F)
            for n in self.stamps_nominal:
                for g in self.stamps_groups[n]:
                    total_num = g*self.stamps_groups[n][g]
                    print("%dx%d=%d p. by %.2f rub."%(self.stamps_groups[n][g], g, total_num, n),file=F)
            


# In[5]:


s = Solver(total_orgs,stamps,list(prices.keys()),total_price);


# In[6]:


s.solve();


# In[7]:


s.print_result("results_test.txt")

