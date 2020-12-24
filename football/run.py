def login_whoscored():
    from selenium import webdriver
    
    browser = webdriver.Chrome('C:\ProgramData\chromedriver.exe')
        
    browser.get('https://www.whoscored.com/Accounts/Login')
    browser.find_element_by_xpath('//*[@id="usernameOrEmailAddress"]').send_keys('damiyan.ivanov@gmail.com')
    browser.find_element_by_xpath('//*[@id="password"]').send_keys('Healbodws752')
    browser.find_element_by_xpath('//*[@id="sign-in-button"]').click()
    
    site_url = 'https://www.whoscored.com/'
    browser.get(site_url)
    return browser

def login_to_db():
    import psycopg2

    con = psycopg2.connect(
      database="football_db", 
      user="healbod", 
      password="Healboddb752",
      host="178.154.233.234", 
      port="5432"
    )

    return con

def close_subscibe():
    from selenium.common.exceptions import NoSuchElementException
    
    try:
        browser.find_element_by_xpath('/html/body/div[7]/div/div[1]/button').click()
        
    except NoSuchElementException:
        pass
    
    
def create_table_all_tours():

    con = login_to_db()

    cur = con.cursor()  
    cur.execute('''CREATE TABLE ALL_TOURS
         (STATUS INTEGER,
         REGION_NAME VARCHAR(255),
         TOUR_NAME VARCHAR(255),
         SEASON_NAME VARCHAR(255),
         STAGE_NAME VARCHAR(255),
         URL TEXT);''')
         
    print("Table created successfully")
    con.commit()  
    con.close()

def delete_table_all_tours():
    
    con = login_to_db()

    cur = con.cursor()  
    cur.execute('''DROP TABLE ALL_TOURS;''')

    print("Table delete successfully")
    con.commit()  
    con.close()
    
# create_table_all_tours()
# delete_table_all_tours()

def find_url_tour_in_db(url):

    con = login_to_db()
    cur = con.cursor()  
    cur.execute('''SELECT URL FROM ALL_TOURS WHERE URL='{}';'''.format(url))
    
    if len(cur.fetchall()) > 0:
        return True
    else:
        return False  

def insert_date_in_all_tours_db(status, region_name, tour_name, season_name, stage_name, url_fixtures):

    cur = con.cursor()
    cur.execute(
      '''INSERT INTO ALL_TOURS (STATUS,
                                REGION_NAME,
                                TOUR_NAME,
                                SEASON_NAME,
                                STAGE_NAME,
                                URL) VALUES ('{}', '{}', '{}', '{}', '{}', '{}')'''.format(
                                status,
                                region_name,
                                tour_name, 
                                season_name, 
                                stage_name, 
                                url_fixtures)
    )

    con.commit()
    
    
from selenium.common.exceptions import TimeoutException

while True:
    try:
        con = login_to_db()

        cur = con.cursor()
        cur.execute("SELECT REGION_NAME,TOUR_NAME,SEASON_NAME,STAGE_NAME,LINK from ALL_TOURS_LINKS")

        rows = cur.fetchall()

        cur.execute('''SELECT STATUS,REGION_NAME,TOUR_NAME,SEASON_NAME,STAGE_NAME,URL
                       FROM ALL_TOURS
                       WHERE STATUS=0''')

        rows_new_db = cur.fetchall()

        browser = login_whoscored()

        for row in rows[(len(rows_new_db)-1):]:


            region_name = row[0]
            tour_name = row[1]
            season_name = row[2]
            stage_name = row[3]
            browser.get(row[4])
            close_subscibe()
            url_fixtures = browser.find_element_by_class_name('with-single-level').find_element_by_link_text('Fixtures').get_attribute('href')
            status = 0
            if not find_url_tour_in_db(url_fixtures):
                insert_date_in_all_tours_db(status, region_name, tour_name, season_name, stage_name, url_fixtures)
            else:
                print('+++++++')
        break
    except TimeoutException:
        browser.quit()