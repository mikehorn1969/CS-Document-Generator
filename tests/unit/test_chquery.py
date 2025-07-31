import json

from app.chquery import getCHRecord

def test_getCHRecord():

    companyNo = "08320269"
        
    #ry:
    company_data = getCHRecord(companyNo)

    print(json.dumps(company_data, indent=2))

    #except Exception as e:
    #    print(f"Failed to get company info: {e}")


if __name__ == "__main__":
    test_getCHRecord()