import fitz 
import re
import os


# at the food page "--delivery-id--" is written each time (in the same colour as the background so invisible)
# this the "split_food_page_pdf" function will split the food page pdf, while keeping the pages with the same
# delivery-id together the result will be a folder which contains the food-pages of the different
# deliveries (filename = --delivery-id)

def split_food_page_pdf(food_page_path, output_directory, pattern):  

    # Open the input PDF using fitz
    doc = fitz.open(food_page_path)
    total_pages = doc.page_count

    booklet_start_pattern = re.compile(pattern)

    # Dictionary to track pages by booklet number
    booklet_pages = {}

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Variable to keep track of the current booklet number
    current_booklet_number = None

    # Iterate through all the pages in the PDF
    for i in range(total_pages):
        page = doc.load_page(i)
        text = page.get_text()

        # Check if the page contains the booklet start pattern (pattern =  r'--\d+--' => --delivery-id--)
        match = booklet_start_pattern.search(text)

        if match:
            # Extract booklet number (= delivery-id) from the matched text
            current_booklet_number = match.group().strip('--')
            print(f"Found pattern: {match.group()}")

            # Initialize a list for this booklet number if not already present
            if current_booklet_number not in booklet_pages:
                booklet_pages[current_booklet_number] = []

        # Add the current page to the current booklet (if we have a current booklet number)
        if current_booklet_number:
            booklet_pages[current_booklet_number].append(i)

    # Function to save a booklet as a PDF
    def save_booklet(pages, booklet_number):
        if not pages:
            return
        # Create a new PDF
        new_pdf = fitz.open()
        for page_num in pages:
            new_pdf.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Create filename with the booklet number surrounded by dashes
        output_pdf_path = os.path.join(output_directory, f"--{booklet_number}--.pdf")
        new_pdf.save(output_pdf_path)
        new_pdf.close()  # Close the new PDF to free resources
        print(f"Saved booklet '{output_pdf_path}' with {len(pages)} pages.")

    # Save each booklet
    for booklet_number, pages in booklet_pages.items():
        save_booklet(pages, booklet_number)
    
    doc.close()  # Close the main PDF to free resources

# the 'insert_food_pages_in_main' function will insert the results of the food-pages split at the appropriate place
# in the main pdf, based on the delivery id
# the front page of the main page contains '--delivery-id--1' (if new customer) or --delivery-id--0'
# (if existing customer) we can include the food page based up on the delivery-id and the 1 or 0 will tell us
# at which place we need to include the food page (new customers have a welcome page, so the delivery page will be
# included one page later)


def insert_food_pages_in_main(main_path, food_pages_path, output_path):

    # Open the large PDF
    main_pdf = fitz.open(main_path)

    # Dictionary to store page ranges for each booklet in the large PDF
    booklet_positions = {}

    # Regex pattern to match the insertion points
    pattern = re.compile(r'--(\d+)--([01])--')

    # Iterate through the large PDF to find booklet insertion points
    for i in range(len(main_pdf)):
        page = main_pdf.load_page(i)
        text = page.get_text("text").strip()  
        match = pattern.search(text) 
        if match:
            number = match.group(1)  # Extract the number part
            flag = match.group(2)  # Extract whether it's 0 or 1
            booklet_positions[number] = (i, flag)  # Store the page index and flag

    # Check if any booklet positions were found
    if not booklet_positions:
        print("No booklet positions found in the large PDF.")
        main_pdf.close()
        return
    
    # Create a list of insertion points sorted by their position
    # Important to sort, such that we go over the delivery-id's in the same order in which they occur in the main-file
    sorted_positions = sorted(booklet_positions.items(), key=lambda x: x[1][0])

    # Track the total number of inserted pages
    # we know at which index we need to include the food-page with the current index, this index will change when we
    # include pages, so we need to track
    # the number of pages that we have included already 

    page_offset = 0

    # Iterate through the sorted insertion points and insert the corresponding files
    for number, (page_index, flag) in sorted_positions:

        # Construct the filename based on the number
        file_name = f'--{number}--.pdf'
        insert_pdf_path = os.path.join(food_pages_path, file_name)

        if os.path.exists(insert_pdf_path):
            print(f'pdf_path: {insert_pdf_path}')
            
            # Calculate the insert position
            if flag == "1": 
                insert_position = page_index + 3 + page_offset

            else:
                insert_position = 2 + page_index + page_offset

            # Open the insert PDF
            insert_pdf = fitz.open(insert_pdf_path)

            # Get the number of pages in the insert PDF
            num_pages = insert_pdf.page_count
            print(f"Inserting {file_name} with {num_pages} pages at position {insert_position}.")

            # Insert the pages into the large PDF
            main_pdf.insert_pdf(insert_pdf, from_page=0, to_page=num_pages - 1, start_at=insert_position)

            # Update the page offset after insertion
            page_offset += num_pages
            
            print(f"Inserted {file_name} at position {insert_position}. Updated page_offset={page_offset}.")

            insert_pdf.close()
        else:
            print(f"File not found: {insert_pdf_path}")

    # Ensure output path is not a directory
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, 'final_booklet.pdf')

    # Save the output PDF
    main_pdf.save(output_path)
    main_pdf.close()

    print(f"Output PDF saved as {output_path}")


def main(): 

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print("Current Working Directory:", os.getcwd())
    
    try:
        input_pdf_path = "./food_pages.pdf"
        output_directory = "./food_pages_output"
        pattern = r'--\d+--'
        split_food_page_pdf(input_pdf_path, output_directory, pattern)
     
        main_path = "./main_template.pdf"
        final_booklet_path = "./final_booklet.pdf"
        insert_food_pages_in_main(main_path, output_directory, final_booklet_path)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__": 
    main()


