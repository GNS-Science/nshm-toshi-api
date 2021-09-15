automation_task = b'''{"id": "8497KNLB",
	"created": "2021-08-28T01:04:52.268255+00:00",
	"files": ["1984UAvDG", "1985TV8oR", "1986GpFtj", "1987tiZUR"],
	"result": "success",
	"state": "done", "duration": 99.15831,
	"parents": ["716tdBQH"],
	"arguments": [{"k": "round", "v": "0"}, {"k": "config_type", "v": "crustal"}, {"k": "rupture_set_file_id", "v": "RmlsZToxNTg3LjBuVm9GdA=="}, {"k": "rupture_set", "v": "/home/chrisbc/DEV/GNS/opensha-new/AWS_S3_DATA/WORKING/downloads/RmlsZToxNTg3LjBuVm9GdA==/RupSet_Cl_FM(CFM_0_9_SANSTVZ_D90)_mnSbS(2)_mnSSPP(2)_mxSSL(0.5)_mxFS(2000)_noInP(T)_slRtP(0.05)_slInL(F)_cfFr(0.75)_cfRN(2)_cfRTh(0.5)_cfRP(0.01)_fvJm(T)_jmPTh(0.001)_cmRkTh(360)_mxJmD(15)_plCn(T)_adMnD(6)_adScFr(0.2)_bi(F)_stGrSp(2)_coFr(0.5).zip"}, {"k": "completion_energy", "v": "0.0"}, {"k": "max_inversion_time", "v": "1"}, {"k": "mfd_equality_weight", "v": "1e2"}, {"k": "mfd_inequality_weight", "v": "1e2"}, {"k": "slip_rate_weighting_type", "v": "BOTH"}, {"k": "slip_rate_weight", "v": ""}, {"k": "slip_uncertainty_scaling_factor", "v": ""}, {"k": "slip_rate_normalized_weight", "v": "1e3"}, {"k": "slip_rate_unnormalized_weight", "v": "1e3"}, {"k": "seismogenic_min_mag", "v": "7.0"}, {"k": "mfd_mag_gt_5_sans", "v": "3.6"}, {"k": "mfd_mag_gt_5_tvz", "v": "0.36"}, {"k": "mfd_b_value_sans", "v": "1.05"}, {"k": "mfd_b_value_tvz", "v": "1.25"}, {"k": "mfd_transition_mag", "v": "7.85"}, {"k": "selection_interval_secs", "v": "1"}, {"k": "threads_per_selector", "v": "4"}, {"k": "averaging_threads", "v": "1"}, {"k": "averaging_interval_secs", "v": "30"}, {"k": "non_negativity_function", "v": "LIMIT_ZERO_RATES"}, {"k": "perturbation_function", "v": "UNIFORM_NO_TEMP_DEPENDENCE"}],
	"environment": [{"k": "host", "v": "tryharder-ubuntu"}, {"k": "gitref_opensha", "v": "865e02cef500cd52c46f816926524439d47698da"}, {"k": "gitref_nzshm-opensha", "v": "190fede64afb81426716e9cd3bb6e8febf59fad0"}, {"k": "gitref_nzshm-runzi", "v": "b8a57184a4307d22e3692c07c33ac1020c26882a"}],
	"metrics": [{"k": "total_ruptures", "v": "507755"}, {"k": "perturbed_ruptures", "v": "7752"}],
	"model_type": null,
	"task_type": "inversion", "clazz_name": "AutomationTask"}'''


file = b'''{"id": "1730.0kpcKK",
	"file_name": "NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6ODQ5N0tOTEI=.zip",
	"md5_digest": "efJKuE5u6l1IT6xrv09RFA==", "file_size": 32902400,
	"file_url": null, "post_url": null,
	"meta": [{"k": "round", "v": "0"}, {"k": "config_type", "v": "crustal"}, {"k": "rupture_set_file_id", "v": "RmlsZToxNTg3LjBuVm9GdA=="}, {"k": "rupture_set", "v": "/home/chrisbc/DEV/GNS/opensha-new/AWS_S3_DATA/WORKING/downloads/RmlsZToxNTg3LjBuVm9GdA==/RupSet_Cl_FM(CFM_0_9_SANSTVZ_D90)_mnSbS(2)_mnSSPP(2)_mxSSL(0.5)_mxFS(2000)_noInP(T)_slRtP(0.05)_slInL(F)_cfFr(0.75)_cfRN(2)_cfRTh(0.5)_cfRP(0.01)_fvJm(T)_jmPTh(0.001)_cmRkTh(360)_mxJmD(15)_plCn(T)_adMnD(6)_adScFr(0.2)_bi(F)_stGrSp(2)_coFr(0.5).zip"}, {"k": "completion_energy", "v": "0.0"}, {"k": "max_inversion_time", "v": "1"}, {"k": "mfd_equality_weight", "v": "1e2"}, {"k": "mfd_inequality_weight", "v": "1e2"}, {"k": "slip_rate_weighting_type", "v": "BOTH"}, {"k": "slip_rate_weight", "v": ""}, {"k": "slip_uncertainty_scaling_factor", "v": ""}, {"k": "slip_rate_normalized_weight", "v": "1e3"}, {"k": "slip_rate_unnormalized_weight", "v": "1e3"}, {"k": "seismogenic_min_mag", "v": "7.0"}, {"k": "mfd_mag_gt_5_sans", "v": "3.6"}, {"k": "mfd_mag_gt_5_tvz", "v": "0.36"}, {"k": "mfd_b_value_sans", "v": "1.05"}, {"k": "mfd_b_value_tvz", "v": "1.25"}, {"k": "mfd_transition_mag", "v": "7.85"}, {"k": "selection_interval_secs", "v": "1"}, {"k": "threads_per_selector", "v": "4"}, {"k": "averaging_threads", "v": "1"}, {"k": "averaging_interval_secs", "v": "30"}, {"k": "non_negativity_function", "v": "LIMIT_ZERO_RATES"}, {"k": "perturbation_function", "v": "UNIFORM_NO_TEMP_DEPENDENCE"}], "relations": ["1987tiZUR"], "created": "2021-08-28T01:06:46.155969+00:00", "metrics": [{"k": "total_ruptures", "v": "507755"}, {"k": "perturbed_ruptures", "v": "7752"}],
	"produced_by_id": "QXV0b21hdGlvblRhc2s6ODQ5N0tOTEI=",
	"mfd_table_id": null, "hazard_table_id": null,
	"tables": [{"label": "Inversion Solution MFD table", "table_id": "VGFibGU6NzVmaUI2dQ==", "table_type": "mfd_curves", "dimensions": null, "identity": "9899efa1-d28d-4708-95ea-9aa1a3135805", "created": "2021-08-28T01:06:57.331200+00:00"}],
	"hazard_table": null, "mfd_table": null, "produced_by": null,
	"clazz_name": "InversionSolution"}'''

file_rel = b'''{"id": "1987tiZUR", "thing": null, "file": null, "role": "write", "thing_id": "8497KNLB",
	"file_id": "1730.0kpcKK", "clazz_name": "FileRelation"}'''