
from client import RestClient
import requests
from config_reader import ConfigReader


def DataForSeo(keyword,region):
    config_reader = ConfigReader()
    configuration = config_reader.read_config()

import time
import requests
import json
from collections import defaultdict

config_reader = ConfigReader()
configuration = config_reader.read_config()

def DataForSeo(keyword,region):
    

    
    
    # You can download this file from here https://cdn.dataforseo.com/v3/examples/python/python_Client.zip
    client = RestClient( configuration['DATA_FOR_SEO_USERNAME'], configuration['DATA_FOR_SEO_API'])


    post_data = dict()
    # simple way to set a task
    post_data[len(post_data)] = dict(
        location_name=region,
        keywords=[keyword],
        
        language_name="English"


    )
    # POST /v3/keywords_data/google_ads/search_volume/live
    # the full list of possible parameters is available in documentation
    response = client.post("/v3/keywords_data/google_ads/search_volume/live", post_data)
    # you can find the full list of the response codes here https://docs.dataforseo.com/v3/appendix/errors
    if response["status_code"] == 20000:
        #print(response)
        dataforseo_result=response
        return dataforseo_result
        # do something with result
    else:
        #print("error. Code: %d Message: %s" % (response["status_code"], response["status_message"]))
        return ("error. Code: %d Message: %s" % (response["status_code"], response["status_message"]))

def scale_serp_api(keyword,country):
    # start_time=time.time()
    
    params = {
    'api_key':configuration['SCALE_SERP_API'],
      'q': keyword,
      'location': country,
      'google_domain': 'google.com',
      'gl': 'us',
      'hl': 'en',
  
      'output': 'json'
        }
    all_page_list_of_dict=[]

    for page in range(1,2):

        params['page']=page
        api_result = requests.get('https://api.scaleserp.com/search', params)
        results_5 = api_result.json()
        all_page_list_of_dict.append(results_5)


    dd = defaultdict(list)

    for d in all_page_list_of_dict: # you can list as many input dicts as you want here
        for key, value in d.items():
            dd[key].append(value)

#     ads=dd['ads']
#     shopping_results=dd['shopping_results']
    
    # end_time=time.time()
    # print('time taken :',end_time-start_time)
    return dict(dd)

def main_output(keyword,country):
    import time
    start_time=time.time()
    try:
                
        dataforseo_result=DataForSeo(keyword,country)
        dataforseo_result=dataforseo_result['tasks'][0]['result'][0]
        scale_serp_results=scale_serp_api(keyword,country)

        try:
            ads_results=scale_serp_results['ads']

        except KeyError:
            try:
                shopping_results=scale_serp_results['inline_shopping']
                output_dict={'keyword':keyword,'scraping_result':{'ads_results':'No Ads for this keyword in this perticular location!','shopping_results':shopping_results},'statistic_information':dataforseo_result}
                print("time taken :",time.time()-start_time)
                return output_dict

            except KeyError:

                output_dict={'keyword':keyword,'scraping_result':{'ads_results':'No Ads for this keyword in this perticular location!','shopping_results':'No shopping results for this keyword in this perticular location'},'statistic_information':dataforseo_result}
                print("time taken :",time.time()-start_time)
                return output_dict

        
        try:
            shopping_results=scale_serp_results['inline_shopping']
            output_dict={'keyword':keyword,'scraping_result':{'ads_results':ads_results,'shopping_results':shopping_results},'statistic_information':dataforseo_result}
            print("time taken :",time.time()-start_time)
            return output_dict
        except KeyError:
            output_dict={'keyword':keyword,'scraping_result':{'ads_results':ads_results,'shopping_results':"No Shopping Results for this keyword in this perticular location."},'statistic_information':dataforseo_result}
            print("time taken :",time.time()-start_time)
            return output_dict
    except TypeError:
            error={'error':"ERROR ! From Server ! There is no data for api"}
            return error
    except Exception as e:
            error={'error':e}
            return error
    



# print(main_output('shoes','united states'))