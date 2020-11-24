# Strong Motion Station

```
mutation create_sms {
  create_strong_motion_station(
    input: {
      created:"2020-11-16T21:35:29.363999+00:00"
    	bedrock_encountered:true
      site_code: "CBGS"
      Vs30_mean:[20.1, 12.33]
    })
   {
    strong_motion_station {
      id
      created
    }
  }
}

query list_sms {
  strong_motion_stations {
    edges {
      node {
        id
        created
        bedrock_encountered
      }
    }
  }
}

query one_sms {
	strong_motion_station(id:"U3Ryb25nTW90aW9uU3RhdGlvbjow") {
    id
    site_code
    created
    Vs30_mean
    bedrock_encountered
    soft_clay_or_peat
    Vs30_std_dev
  }
}


query search_SMS {
  search(
    search_term: "CBGS"
  	#search_term: "bedrock_encountered:true"
  	)
    {
    search_result {
      edges {
        node {
					... on File {
            id
            site_code
            bedrock_encountered
            created
          }

        }
      }
    }
  }
}

```

## after file upload
```
query one_sms_CBGS {
  strong_motion_station(id:"U3Ryb25nTW90aW9uU3RhdGlvbjow") {
    id
    site_code
    created
    Vs30_mean
    bedrock_encountered
    soft_clay_or_peat
    Vs30_std_dev
    files {
      edges {
        node {
        __typename
        ... on SmsFileLink {
          file_type
          file {
            file_name
            file_size
          }
        }
      }
    }
  }
  }
}

```