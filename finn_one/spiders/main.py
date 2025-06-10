import scrapy
from finn_one.items import Product
from lxml import html
import os
from email import message_from_string
from email.policy import default
import quopri

def parse1(response):
    res_text = response.text.replace('=3D', '=').replace('=20', ' ').replace('=09', '\t')
    parser = html.fromstring(res_text)
    xpath_address_lists = '//table[@id="addressDetailsDiv"]/tbody//tr'
    address_lists_dict = {}
    c = 0
    cif_cid = ''.join(
        parser.xpath("//label[contains(text(), 'CIF#')]//parent::div/text()")
    )
    cif_cid = ''.join(
        [i.strip() for i in cif_cid if i.strip()]
    ) if cif_cid else ''
    for address in parser.xpath(xpath_address_lists):
        c+=1
        address_type = address.xpath(".//td[@code='addressTypeCheckBox']//span//text()")
        # print(address.xpath(".//td[@id='customerContactAddress']//span//text()"))
        # print(address.xpath(".//td[@code='phoneNumberCheckBox']/span/text()"))
        if 'Office/ Business Address' in address_type:
            address_lists_dict['Office_address'] = quopri.decodestring(''.join(
                address.xpath(".//td[@id='customerContactAddress']//span//text()")
                )).decode('utf-8').strip() if 'Office/ Business Address' in address_type else ''
            address_lists_dict['phone_number_office'] = ''.join(
                address.xpath(".//td[@code='phoneNumberCheckBox']//span//text()")
            ).strip()
        if 'Residential Address' in address_type:
            address_lists_dict[f'Residential_address_{c}'] = quopri.decodestring(''.join(
                address.xpath(".//td[@id='customerContactAddress']//span//text()")
                )).decode('utf-8').strip() if 'Residential Address' in address_type else ''
            
            address_lists_dict[f"phone_number_residential_{c}"] = ''.join(
                address.xpath(".//td[@code='phoneNumberCheckBox']//span//text()")
            ).strip()
    address_lists_dict['cif_cid'] = cif_cid if cif_cid else ''
    return address_lists_dict

class Finn_oneSpider(scrapy.Spider):
    name = "finn_one"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.finn_uae_list = []       # For main files
        self.finn_uae_sub_list = []   # For sub files
        self.total_requests = 0       # Track total files to process
        self.processed_responses = 0  # Track responses received
    
    def start_requests(self):
        folder_path = os.path.dirname(os.path.abspath(__file__))
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".mhtml"):
                # print(file_name)
                self.total_requests += 1
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                yield scrapy.Request(
                    url='file://' + file_path,
                    callback=self.parse,
                    meta={
                        'file_name': file_name,
                        'raw_mhtml': content
                    }
                )

    def parse(self, response):
        file_name = response.meta.get('file_name')
        finn_uae_list, finn_uae_sub_list = [], []
        if file_name:
            
            if '_Contact' in file_name:
                finn_uae = parse1(response)
                if finn_uae:
                # yield Product(**{'res': finn_uae})
                    self.finn_uae_list.append(finn_uae)
            elif 'Info' in file_name:
                finn_uae_sub = self.parse2(response, response.meta)
                if finn_uae_sub:
                    self.finn_uae_sub_list.append(finn_uae_sub)
            # else:
            #     finn_uae_sub = self.parse2(response, response.meta)
            #     if finn_uae_sub:
            #         self.finn_uae_sub_list.append(finn_uae_sub)

        self.processed_responses += 1
        if self.processed_responses == self.total_requests:
            # Only proceed if there is data to compare
            # print(finn_uae_list)
            if self.finn_uae_list and self.finn_uae_sub_list:
                for item in self.generate_items():
                    yield Product(**item)
                    # print(item)
            else:
                print("No data found in one or both lists")


    def parse2(self, response, meta):
        mhtml_raw = meta['raw_mhtml']

        # Step 1: Parse as email
        msg = message_from_string(mhtml_raw, policy=default)

        # Step 2: Extract the HTML part
        html_body = None
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html':
                    html_body = part.get_content()
                    break
        else:
            if msg.get_content_type() == 'text/html':
                html_body = msg.get_content()

        if not html_body:
            self.logger.warning("No HTML found in: %s", response.url)
            return

        # Step 3: Parse HTML with lxml
        parser = html.fromstring(html_body)

        # Step 3: Parse HTML with lxml
        # parser = html.fromstring(response.text)
        # print(html_body)

        # Sample extraction
        passport_no = ''.join(
            parser.xpath("//div[contains(text(), 'Passport No.')]/following-sibling::div[1]/text()")
        )
        gender = ''.join(
            parser.xpath("//div[contains(text(), 'Applicants Gender')]/following-sibling::div[1]/text()")
        )
        national_id = ''.join(
            parser.xpath("//div[contains(text(), 'National ID')]/following-sibling::div[1]/text()")
        )
        date_of_birth = ''.join(
            parser.xpath("//div[contains(text(), 'Date of Birth')]/following-sibling::div[1]/text()")
        )
        marital_status = ''.join(
            parser.xpath("//div[contains(text(), 'Marital Status')]/following-sibling::div[1]/text()")
        )
        nationality = ''.join(
            parser.xpath("//div[contains(text(), 'Nationality')]/following-sibling::div[1]/text()")
        )
        salary = ''.join(
            parser.xpath("//div[contains(text(), 'Salary')]/following-sibling::div[1]/text()")
        )
        branch_name = ''.join(
            parser.xpath("//div[contains(text(), 'Branch Name')]/following-sibling::div[1]/text()")
        )
        Current_Organisation = ''.join(
            parser.xpath("//div[contains(text(), 'Current Organisation')]/following-sibling::div[1]/text()")
        )
        Previous_Organisation = ''.join(
            parser.xpath("//div[contains(text(), 'Previous Organisation')]/following-sibling::div[1]/text()")
        )
        Emirates_ID_Expiry_Date = ''.join(
            parser.xpath("//div[contains(text(), 'Emirates ID Expiry Date')]/following-sibling::div[1]/text()")
        )
        Visa_Expiry_Date = ''.join(
        parser.xpath("//div[contains(text(), 'Visa Expiry Date')]/following-sibling::div[1]/text()")
        )
        Passport_Expiry_Date = ''.join(
            parser.xpath("//div[contains(text(), 'Passport Expiry Date')]/following-sibling::div[1]/text()")
        )
        Date_of_joining = ''.join(
            parser.xpath("//div[contains(text(), 'Date of joining')]/following-sibling::div[1]/text()")
        )
        cif_cid = ''.join(
            parser.xpath("//label[contains(text(), 'CIF#')]//parent::div/text()")
        )
        cif_cid = ''.join(
            [i.strip() for i in cif_cid if i.strip()]
        ) if cif_cid else ''
        card_number = ''.join(
            parser.xpath("//div[contains(text(), 'Card Number')]/following-sibling::div[1]/text()")
        )
        total_amount_overdue = ''.join(
            parser.xpath("//label[contains(text(), ' Total Amount Overdue')]//parent::div/text()")
        )
        Total_Balance_Outstanding = ''.join(
            parser.xpath("//label[contains(text(), 'Total Balance Outstanding')]//parent::div/text()")
        )
        from datetime import date
        scrape_date = date.today()
        data = {
            'passport_no': passport_no if passport_no else '',
            'gender': gender if gender else '',
            'national_id': national_id if national_id else '',
            'date_of_birth': date_of_birth if date_of_birth else '',
            
            'marital_status': marital_status if marital_status else '',
            'nationality': nationality if nationality else '',
            'salary': salary if salary else '',
            'branch_name': branch_name if branch_name else '',
            'Current_Organisation': Current_Organisation if Current_Organisation else '',
            'Previous_Organisation': Previous_Organisation if Previous_Organisation else '',
            'Emirates_ID_Expiry_Date': Emirates_ID_Expiry_Date if Emirates_ID_Expiry_Date else '',
            'Visa_Expiry_Date': Visa_Expiry_Date if Visa_Expiry_Date else '',
            'Passport_Expiry_Date': Passport_Expiry_Date if Passport_Expiry_Date else '',
            'Date_of_joining': Date_of_joining if Date_of_joining else '',
            'cif_cid': cif_cid if cif_cid else '',
            
            'card_number': card_number if card_number else '',
            'total_amount_overdue': total_amount_overdue if total_amount_overdue else '',
            'Total_Balance_Outstanding': Total_Balance_Outstanding if Total_Balance_Outstanding else '',
            'scrape_date': scrape_date
        }
        return data


    def generate_items(self):
        items = []
        if self.finn_uae_list and self.finn_uae_sub_list:
            for main in self.finn_uae_list:
                for sub in self.finn_uae_sub_list:
                    if main.get('cif_cid') == sub.get('cif_cid'):
                        combined = {**main, **sub}
                        items.append(combined)
        return items  # Always returns an empty list if no matches