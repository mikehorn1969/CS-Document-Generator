# classes.py
# classes for use in cs_contracts app
from app import db

class Config:

    _instances = []

    def __init__(self, key, value ):
        self.key = key
        self.value = value
        Config._instances.append(self)
        
    @classmethod
    def find_by_name(cls, search_name):
        for search_config in cls._instances:
            if search_config.key == search_name:
                return search_config.value
        return None


class Company:

    counter = 0
    _instances = []

    def __init__(self, companyname, address, email, phone, companyNumber):
        self.companyname = companyname
        self.address = address
        self.emailaddress = email
        self.phone = phone
        self.companyNumber = companyNumber
        Company.counter += 1 # increment the company counter
        Company._instances.append(self)

    @classmethod
    def count(cls):
        print(f"Company count: {cls.counter}")

    
    @classmethod
    def find_by(cls, field, value):
        for search_company in cls._instances:
            attr = getattr(search_company,field, None)
            if isinstance(attr, set) and len(attr) == 1:
                attr = next(iter(attr))
            if attr == value:
                return search_company
        return None
    
    @classmethod
    def get_all_companies(cls):
        return cls._instances

class Contact:

    counter = 0
    _instances = []

    def __init__(self, companyname, name, address, emailaddress, phone, title  ):        
        self.companyname = companyname
        self.name = name
        self.address = address
        self.emailaddress = emailaddress
        self.phone = phone
        self.title = title
        
        Contact.counter += 1 # increment the company counter
        Contact._instances.append(self)

    @classmethod
    def count(cls):
        print(f"Contact count: {cls.counter}")

    @classmethod
    def get_all_contacts(cls):
        return cls._instances
    
    @classmethod
    def find_by_name(cls, search_name):
        for search_contact in cls._instances:
            if search_contact.name == search_name:
                return search_contact
        return None    
    
    @classmethod
    def find_by_company(cls, search_company):
        contacts = []
        for search_contact in cls._instances:
            if search_contact.company_name == search_company:
                contacts.append(search_contact)
        
        if contacts is None:
            return None    
        else:
            return contacts

    @classmethod
    def find_by(cls, field, value):
        for search_contact in cls._instances:
            attr = getattr(search_contact,field, None)
            """ if isinstance(attr, set) and len(attr) == 1:
                attr = next(iter(attr)) """
            if attr == value:
                return search_contact
        return None

class Requirement:

    counter = 0
    _instances = []

    def __init__(self, requirementid, companyname, contactname, description, jobtitle ):        
        self.requirementId = requirementid
        self.companyname = companyname
        self.contactname = contactname
        self.description = description
        self.jobtitle = jobtitle
        
        Requirement.counter += 1 # increment the company counter
        Requirement._instances.append(self)

    @classmethod
    def count(cls):
        print(f"Requirement count: {cls.counter}")

    @classmethod
    def get_all_contacts(cls):
        return cls._instances
    
    @classmethod
    def find_by_name(cls, search_name):
        for search_contact in cls._instances:
            if search_contact.name == search_name:
                return search_contact
        return None    
    
    @classmethod
    def find_by_company(cls, search_company):
        requirements = []
        for search_contact in cls._instances:
            if search_contact.company_name == search_company:
                requirements.append(search_contact)
        
        if requirements is None:
            return None    
        else:
            return requirements
        
    @classmethod
    def find_by(cls, field, value):
        for search_requirement in cls._instances:            
            if getattr(search_requirement,field, None) == value:
                return search_requirement
        return None

class Candidate:

    counter = 0
    _instances = []

    def __init__(self, candidatetid, candidatename):        
        self.candidateId = candidatetid
        self.candidateName = candidatename
        self.companyNumber = ''
        
        Candidate.counter += 1 # increment the company counter
        Candidate._instances.append(self)

    @classmethod
    def count(cls):
        print(f"Candidate count: {cls.counter}")

    @classmethod
    def get_all_candidates(cls):
        return cls._instances
    
    @classmethod
    def find_by_name(cls, search_name):
        for search_candidate in cls._instances:
            if search_candidate.name == search_name:
                return search_candidate
        return None    
    
    @classmethod
    def find_by(cls, field, value):
        for search_candidate in cls._instances:

            c_attr = getattr(search_candidate,field, None)
            c_attr = str(c_attr).strip("{}").strip('"').strip("'")
            
            if c_attr == value:
                return search_candidate
        return None
    
