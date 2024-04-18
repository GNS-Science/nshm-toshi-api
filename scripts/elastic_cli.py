import os
import sys

import click
import logging
import boto3

from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from elasticsearch_dsl import Q, Search, connections


from graphql_relay import to_global_id
from graphql_api.config import ES_ENDPOINT

ES_REGION = 'ap-southeast-2'

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        ES_REGION,
        'es',
        session_token=credentials.token)

es = Elasticsearch(
    hosts=[ES_ENDPOINT],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

connections.add_connection('default', es)


log = logging.getLogger()
logging.basicConfig(level=logging.WARN)
logging.getLogger('elsaticsearch').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
file_handler = logging.FileHandler('slt.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
log.addHandler(screen_handler)
log.addHandler(file_handler)


@click.group()
def main():
    pass


@main.command(name='ohs')
@click.option(
    '-f', '--filter', type=click.Choice(['DAG', 'HAZ'], case_sensitive=False), help='list filter solutions by subtype.'
)
@click.option(
    '-l', '--list-ids', is_flag=True, default=False, help="list the toshi_ids, with no aggregation (verbose option)."
)
@click.option('-v', '--verbose', is_flag=True, default=False, help='print extra information.')
def cli_OHS(filter, list_ids, verbose):
    """Get OpenquakeHazardSolution hits - either hazard or disagg."""
    s = Search()
    qFilter = Q("term", meta__k="hazard_agg_target")  # this marks a disagg
    qClass = Q("term", clazz_name__keyword="OpenquakeHazardSolution")
    if filter and filter == 'DAG':
        if verbose:
            click.echo('GET disagggregation solutions')
    elif filter and filter == 'HAZ':
        if verbose:
            click.echo('GET hazard solutions')
        qFilter = ~qFilter  # invert for hazard / non-disaggs

    expr = qClass & qFilter if filter else qClass
    s = s.query(expr)

    # the shortform, just dump the ids to stdout
    if list_ids:
        for hit in s.execute():
        # for hit in s.scan():

            if verbose:
                click.echo(f'{to_global_id(hit.clazz_name, hit.id)}, {hit.clazz_name}, {hit.id}')
            else:
                click.echo(to_global_id(hit.clazz_name, hit.id))
        return

    # the longform, aggregate by month ...
    s.aggs.bucket('solutions_per_month', 'date_histogram', field='created', interval='month')
    s = s.extra(explain=True, track_total_hits=True)

    if verbose:
        click.echo('query')
        click.echo(s.to_dict())

    s = s[:2]

    response = s.execute()
    click.echo(f'Total {response.hits.total.value} hits found.')
    click.echo()
    for bucket in response.aggregations.solutions_per_month.buckets:
        click.echo(f'{bucket.key_as_string}, {bucket.doc_count}')

    if verbose:
        for hit in response:
            click.echo(f'{hit}, {hit.created}, {hit.clazz_name}')


@main.command(name='n_is')
@click.option(
    '-f', '--flip', is_flag=True, help='flip 2nd term'
)
@click.option('-c', '--clazz', default="AutomationTask")
@click.option('-t', '--task_type', default="inversion")
@click.option(
    '-l', '--list-ids', is_flag=True, default=False, help="list the toshi_ids, with no aggregation (verbose option)."
)
@click.option('-v', '--verbose', is_flag=True, default=False, help='print extra information.')
def cli_nis(flip, clazz, task_type, list_ids, verbose):
    """Get Inversion Solution sttsu."""
    s = Search()
    # qFilter = Q("term", meta__k="hazard_agg_target")  # this marks a disagg
    # qClass = Q("term", clazz_name__keyword="InversionSolution")
    qClass = Q("term", clazz_name__keyword=clazz)
    # q2 = Q("term", task_type__keyword=task_type)

    #flip 2nd term
    expr = qClass #  & ~q2 if flip else qClass & q2

    s = s.query(expr)
    # explicitly include/exclude fields
    # s = s.source(excludes=["arguments.*", "files.*"])    # "meta.*",
    s = s.extra(track_total_hits=True)
    #for hit in s.execute():
    for hit in s.scan():
        tt = hit.to_dict().get('task_type')
        res = f"{to_global_id(hit.clazz_name, hit.id)}\t{hit.created}\t{tt}\t{hit.result}"
        if hit.duration:
            res += f"\t{hit.duration/3600}"
        click.echo(res)


    print( hit.to_dict())

    if list_ids and verbose:
        response = s.execute()
        click.echo(f'Total {response.hits.total.value} hits found.')
    return



if __name__ == '__main__':
    main()  # pragma: no cover
