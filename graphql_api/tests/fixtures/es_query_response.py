response_01 = b'''{
    "took": 29,
    "timed_out": false,
    "_shards": {
        "total": 5,
        "successful": 5,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": 135,
        "max_score": 5.8634133,
        "hits": [
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "FileData_282_object.json",
                "_score": 5.8634133,
                "_source": {
                    "id": "282",
                    "file_name": "ruptset_ddw0.5_jump5.3_ALL_560.0_3_DOWNDIP.zip",
                    "md5_digest": "bYjNwc0n98D3DlslRmmxsg==",
                    "file_size": 21880998,
                    "file_url": null,
                    "post_url": null,
                    "things": [
                        "560"
                    ]
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "FileData_560_object.json",
                "_score": 4.781921,
                "_source": {
                    "id": "560",
                    "file_name": "ruptset_ddw1.0_jump4.0_SANS_TVZ2_580.0_3_DOWNDIP.zip",
                    "md5_digest": "obk9j+pFjgtXryIGNa6RCg==",
                    "file_size": 1977314,
                    "file_url": null,
                    "post_url": null,
                    "things": [
                        "1114"
                    ]
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_560_object.json",
                "_score": 4.765019,
                "_source": {
                    "id": "560",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-13T14:28:49.019800+00:00",
                    "duration": 209.849867,
                    "files": [
                        "1119",
                        "1120"
                    ],
                    "arguments": {
                        "max_jump_distance": 4,
                        "max_sub_section_length": 0.5,
                        "min_sub_sections_per_parent": 2,
                        "max_cumulative_azimuth": 600,
                        "permutation_strategy": "downdip"
                    },
                    "metrics": {
                        "rupture_count": 356219,
                        "subsection_count": 2596,
                        "cluster_connection_count": 1432
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_280_object.json",
                "_score": 4.1484118,
                "_source": {
                    "id": "280",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T12:48:59.599283+00:00",
                    "duration": 259.644077,
                    "files": [
                        "559",
                        "560"
                    ],
                    "arguments": {
                        "max_jump_distance": 5.3,
                        "max_sub_section_length": 0.5,
                        "min_sub_sections_per_parent": 3,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "downdip"
                    },
                    "metrics": {
                        "rupture_count": 412031,
                        "subsection_count": 3238,
                        "cluster_connection_count": 3240
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_262_object.json",
                "_score": 1,
                "_source": {
                    "id": "262",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T10:32:21.533653+00:00",
                    "duration": 264.873376,
                    "files": [
                        "523",
                        "524"
                    ],
                    "arguments": {
                        "max_jump_distance": 5.2,
                        "max_sub_section_length": 0.5,
                        "min_sub_sections_per_parent": 3,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "downdip"
                    },
                    "metrics": {
                        "rupture_count": 382661,
                        "subsection_count": 3238,
                        "cluster_connection_count": 3180
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_278_object.json",
                "_score": 1,
                "_source": {
                    "id": "278",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T12:29:36.100094+00:00",
                    "duration": 320.450918,
                    "files": [
                        "555",
                        "556"
                    ],
                    "arguments": {
                        "max_jump_distance": 5.3,
                        "max_sub_section_length": 0.5,
                        "min_sub_sections_per_parent": 2,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "downdip"
                    },
                    "metrics": {
                        "rupture_count": 1622624,
                        "subsection_count": 3238,
                        "cluster_connection_count": 3240
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_300_object.json",
                "_score": 1,
                "_source": {
                    "id": "300",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T15:09:59.315824+00:00",
                    "duration": 228.860422,
                    "files": [
                        "599",
                        "600"
                    ],
                    "arguments": {
                        "max_jump_distance": 0.75,
                        "max_sub_section_length": 0.5,
                        "min_sub_sections_per_parent": 4,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "points"
                    },
                    "metrics": {
                        "rupture_count": 16714,
                        "subsection_count": 3238,
                        "cluster_connection_count": 1214
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_315_object.json",
                "_score": 1,
                "_source": {
                    "id": "315",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T16:30:05.414618+00:00",
                    "duration": 399.309633,
                    "files": [
                        "629",
                        "630"
                    ],
                    "arguments": {
                        "max_jump_distance": 1,
                        "max_sub_section_length": 1,
                        "min_sub_sections_per_parent": 2,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "points"
                    },
                    "metrics": {
                        "rupture_count": 31465,
                        "subsection_count": 1913,
                        "cluster_connection_count": 1370
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_319_object.json",
                "_score": 1,
                "_source": {
                    "id": "319",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T16:51:23.892729+00:00",
                    "duration": 398.669986,
                    "files": [
                        "637",
                        "638"
                    ],
                    "arguments": {
                        "max_jump_distance": 1,
                        "max_sub_section_length": 1,
                        "min_sub_sections_per_parent": 4,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "points"
                    },
                    "metrics": {
                        "rupture_count": 3842,
                        "subsection_count": 1913,
                        "cluster_connection_count": 1370
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            },
            {
                "_index": "toshi_index",
                "_type": "_doc",
                "_id": "TaskData_317_object.json",
                "_score": 1,
                "_source": {
                    "id": "317",
                    "result": "success",
                    "state": "done",
                    "started": "2020-11-12T16:40:47.695422+00:00",
                    "duration": 398.189321,
                    "files": [
                        "633",
                        "634"
                    ],
                    "arguments": {
                        "max_jump_distance": 1,
                        "max_sub_section_length": 1,
                        "min_sub_sections_per_parent": 3,
                        "max_cumulative_azimuth": 560,
                        "permutation_strategy": "points"
                    },
                    "metrics": {
                        "rupture_count": 9852,
                        "subsection_count": 1913,
                        "cluster_connection_count": 1370
                    },
                    "git_refs": {
                        "opensha_ucerf3": "ec9409f9fccc69ba7e7f11ce5628316eb13f716f",
                        "opensha_commons": "499df975b11d4d5e204bc35be8bfd42d87b47359",
                        "opensha_core": "8619e9d75cfae4d22e12aff4bdc9f161100986bb",
                        "nshm_nz_opensha": "40d4138b02bc0b6af5b8e28f1b86996659278304"
                    }
                }
            }
        ]
    }
}'''