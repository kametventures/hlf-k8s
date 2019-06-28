import glob
import os
import json
import time
from subprocess import call


from utils.cli import init_cli
from utils.run_utils import Client

SUBSTRA_PATH = '/substra'


def add_org_with_channel():
    # make current org in consortium of system channel for being able to create channel
    config_tx_file = client.createSystemUpdateProposal()
    client.signAndPushSystemUpdateProposal(config_tx_file)
    time.sleep(2)  # raft time

    # generate channel configuration from configtx.yaml + anchor peer configuration for future update
    client.generateChannelArtifacts()
    # create channel
    client.createChannel()
    time.sleep(2)  # raft time

    # make peers join channel
    client.peersJoinChannel()

    # update anchor peers
    client.updateAnchorPeers()

    # Install chaincode on peer in each org
    client.installChainCodeOnPeers(conf, conf['misc']['chaincode_version'])

    # Instantiate chaincode on peers (could be done on only one peer)
    client.instanciateChaincode()

    # Query chaincode from the 1st peer of the 1st org
    if client.queryChaincodeFromPeers() == 'null':
        print('Congratulations! Ledger has been correctly initialized.', flush=True)
        call(['touch', conf['misc']['run_success_file']])
    else:
        print('Fail to initialize ledger.', flush=True)
        call(['touch', conf['misc']['run_fail_file']])


def add_org():
    # update channel for making it know new org (anhcor peers are directly included)
    client.generateChannelUpdate(conf, conf_externals)
    time.sleep(2)  # raft time

    # make peers join channel
    client.peersJoinChannel()

    # update chaincode version, as new org
    chaincode_version = client.getChaincodeVersion(conf_externals[0])
    new_chaincode_version = '%.1f' % (chaincode_version + 1.0)

    # Install chaincode on peer in each org
    orgs_mspid = []
    for conf_org in [conf] + conf_externals:
        client.installChainCodeOnPeers(conf_org, new_chaincode_version)
        orgs_mspid.append(conf_org['mspid'])

    # upgrade chaincode with new policy
    client.upgradeChainCode(conf_externals[0], orgs_mspid, new_chaincode_version, 'init')

    # Query chaincode from the 1st peer of the 1st org
    if client.queryChaincodeFromPeers() == 'null':
        print('Congratulations! Ledger has been correctly initialized.', flush=True)
        call(['touch', conf['misc']['run_success_file']])
    else:
        print('Fail to initialize ledger.', flush=True)
        call(['touch', conf['misc']['run_fail_file']])


if __name__ == "__main__":

    org_name = os.environ.get("ORG")

    conf = json.load(open('/substra/conf/config/conf-%s.json' % org_name, 'r'))
    conf_orderer = json.load(open('/substra/conf/config/conf-orderer.json', 'r'))

    # TODO use Discovery API
    if os.path.exists(conf['misc']['channel_tx_file']):
        files = glob.glob('/substra/conf/config/conf-*.json')

        # Hack to get running org
        # TODO use Discovery API
        runs = glob.glob('/substra/data/log/run-*.successful')
        successful_orgs = [file_path.split('/substra/data/log/run-')[-1].split('.successful')[0] for file_path in runs]

        files = [file_path for file_path in files
                 if file_path.split('/substra/conf/config/conf-')[-1].split('.json')[0] in successful_orgs]

        conf_externals = [json.load(open(file_path, 'r')) for file_path in files]

        cli = init_cli(conf_externals + [conf, conf_orderer])

        # make new org know channel already created
        cli.new_channel(conf['misc']['channel_name'])

        client = Client(cli, conf, conf_orderer)
        add_org()
    else:
        cli = init_cli([conf, conf_orderer])
        client = Client(cli, conf, conf_orderer)
        add_org_with_channel()
