from pprint import pprint

from lark import Lark
from lark import Transformer

s2d_grammar = r"""
    ?value: e
          | role
          | DIGIT -> number

    dot: "."
    dash: "-"
    name: /[\w\d\-\$\&\+\,\:\;\=\?\@\#\|\<\>\^\*\(\)\%\!]+/
    mspid: WORD
    role: "'" name dot mspid "'"
    
    or: "OR"
    and: "AND"
    outof: "OutOf"
    logic: or | and | outof
    
    e : logic "(" [value ("," value)*] ")"


    %import common.WORD
    %import common.LETTER
    %import common.DIGIT
    %import common.WS
    %ignore WS

    """


class StringToDict(Transformer):
    id = 0
    roles = []

    def unique_list_of_dict(self, l):
        unique_l = []

        for item in l:
            if item not in unique_l:
                unique_l.append(item)

        return unique_l

    def get_logic(self, args, n):

        identities = []
        policies = []

        for i, v in enumerate(args):
            if 'policy' in v:
                identities += v['identities']
                policies.append(v['policy'])
            else:
                identities.append({"role": {'name': v['name'], 'mspId': v['mspId']}})
                policies.append({"signed-by": v['id']})

        return {
            "identities": self.unique_list_of_dict(identities),
            "policy": {
                f"{n}-of": policies
            }
        }

    def get_outof(self, items):
        digit, *args = items
        return self.get_logic(args, digit)

    def name(self, items):
        return ''.join(items)

    def role(self, items):
        mspId, dot, name = items

        # check if identity already exists in self.identities
        for role in self.roles:
            if role['name'] == name and role['mspId'] == mspId:
                break
        else:
            role = {"name": name, "mspId": mspId, "id": self.id}
            self.id += 1
            self.roles.append(role)

        return role

    def logic(self, items):
        logic, = items
        return logic.data

    def e(self, items):
        logic, *args = items

        if logic == 'or':
            return self.get_logic(args, 1)
        elif logic == 'and':
            return self.get_logic(args, len(args))
        elif logic == 'outof':
            return self.get_outof(args)

        return items

    dot = lambda self, _: '.'
    dash = lambda self, _: '-'
    mspid = lambda self, s: str(s[0])
    number = lambda self, s: int(s[0])


class Dict2String(object):
    roles = []

    def get_policy(self, policy):
        policy_key = list(policy.keys())[0]
        n = policy_key.split('-of')[0]

        roles = []
        subpolicies = []

        if isinstance(policy[policy_key], list):
            for p in policy[policy_key]:
                key = list(p.keys())[0]
                if key == 'signed-by':
                    r = self.roles[p[key]]
                    roles.append(r)
                else:
                    p = self.get_policy(p)
                    subpolicies.append(p)
        else:
            n = 1
            subpolicies = [self.roles[policy[policy_key]]]

        return f"OutOf({n}, {', '.join(roles)}{', '.join(subpolicies)})"

    def parse(self, d):
        self.roles = [f"'{x['role']['mspId']}.{x['role']['name']}'" for x in d['identities']]

        return self.get_policy(d['policy'])


s2d = Lark(s2d_grammar, start='value', parser='lalr', transformer=StringToDict())
d2s = Dict2String()



# outof_or = "OutOf(1, 'Org1.member', 'Org2.member')"
# # is equivalent to
# ore = "OR('Org1.member', 'Org2.member')"
#
# outof_and = "OutOf(2, 'Org1.member', 'Org2.member')"
# # is equivalent to
# ande = "AND('Org1.member', 'Org2.member')"
#
# outof_complex = "OutOf(2, 'Org1.member', 'Org2.member', 'Org3.member')"
# # is equivalent to
# complex = "OR(AND('Org1.member', 'Org2.member'), AND('Org1.member', 'Org3.member'), AND('Org2.member', 'Org3.member'))"
#
# _1ofAny = "OR('Org1.member', 'Org2.member', 'Org1.admin', 'Org2.admin')"
#
# _1AdminOr2Other = "OR(AND('Org1.member', 'Org2.member'), 'Org1.admin', 'Org2.admin')"
#
# _2ofAny = "OutOf(2, 'Org1.member', 'Org2.member', 'Org1.admin', 'Org2.admin')"

# print(ore)
# pprint(s2d.parse(ore))
#
# print(outof_or)
# pprint(s2d.parse(outof_or))
#
# print(ande)
# pprint(s2d.parse(ande))
#
# print(outof_and)
# pprint(s2d.parse(outof_and))
#
# print(complex)
# pprint(s2d.parse(complex))
#
# print(outof_complex)
# pprint(s2d.parse(outof_complex))

# print(_1ofAny)
# pprint(s2d.parse(_1ofAny))

# print(_1AdminOr2Other)
# pprint(s2d.parse(_1AdminOr2Other))

# print(_2ofAny)
# pprint(s2d.parse(_2ofAny))

# {
# 	"1ofAny": {
# 		"identities": [
# 			{ "role": { "name": "member", "mspId": "Org1MSP" }},
# 			{ "role": { "name": "member", "mspId": "Org2MSP" }},
# 			{ "role": { "name": "admin", "mspId": "Org1MSP" }},
# 			{ "role": { "name": "admin", "mspId": "Org2MSP" }}
# 		],
# 		"policy": {
# 			"1-of": [{ "signed-by": 0}, { "signed-by": 1 }, { "signed-by": 2 }, { "signed-by": 3}]
# 		}
# 	},
# 	"1AdminOr2Other": {
# 			"identities": [
# 				{ "role": { "name": "member", "mspId": "Org1MSP" }},
# 				{ "role": { "name": "member", "mspId": "Org2MSP" }},
# 				{ "role": { "name": "admin", "mspId": "Org1MSP" }},
# 				{ "role": { "name": "admin", "mspId": "Org2MSP" }}
# 			],
# 			"policy": {
# 				"1-of": [
# 					{ "signed-by": 2},
# 					{ "signed-by": 3},
# 					{ "2-of": [{ "signed-by": 0}, { "signed-by": 1 }]}
# 				]
# 			}
# 	},
# 	"2ofAny": {
# 		"identities": [
# 			{ "role": { "name": "member", "mspId": "Org1MSP" }},
# 			{ "role": { "name": "member", "mspId": "Org2MSP" }},
# 			{ "role": { "name": "admin", "mspId": "Org1MSP" }},
# 			{ "role": { "name": "admin", "mspId": "Org2MSP" }}
# 		],
# 		"policy": {
# 			"2-of": [{"signed-by": 0}, {"signed-by": 1}, {"signed-by": 2}, {"signed-by": 3}]
# 		}
# 	}
# }


# policy = {'identities': [{'role': {'name': 'member', 'mspId': 'chu-nantesMSP'}}], 'policy': {'signed-by': 0}}
# print(d2s.parse(policy))

# ore = s2d.parse(ore)
# pprint(ore)
# print(p.s2d(ore))
#
# ande = s2d.parse(ande)
# pprint(ande)
# print(p.s2d(ande))

# outof_complex = s2d.parse(outof_complex)
# pprint(outof_complex)
# print(p.s2d(outof_complex))
#
# complex = s2d.parse(complex)
# pprint(complex)
# complex = d2s.parse(complex)
# print(complex)
# complex = s2d.parse(complex)
# pprint(complex)
