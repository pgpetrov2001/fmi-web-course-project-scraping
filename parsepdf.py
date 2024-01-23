import sys

def plot_tables(tables):
    import matplotlib.pyplot as plt
    curr_page = 1
    for table in tables:
        if table.page == curr_page:
            camelot.plot(table, kind='contour')
            plt.show()
            curr_page += 1
        camelot.plot(table, kind='grid')
        plt.show()

def show_tables(tables):
    import pandas as pd
    import matplotlib.pyplot as plt
    for table in tables:
        fix, ax = plt.subplots()
        ax.axis('off')
        table = pd.plotting.table(ax, table.df, loc='center', cellLoc='center')
        plt.show()

def show_html(tables):
    for table in tables:
        print(table.df.to_html())

def parse1(file, **kwargs):
    import camelot
    tables = camelot.read_pdf(file, pages='all', **kwargs)
    tables = tables[1:-1] # logo gets interpreted as a table
    avg_accuracy = 0
    for i, table in enumerate(tables):
        avg_accuracy += table.parsing_report['accuracy']
        #print(f'table {i} on page {table.page}', file=sys.stderr)
        #print(table.parsing_report)
    avg_accuracy /= len(tables)
    print(avg_accuracy, file=sys.stderr)

    #plot_tables(tables)
    #show_tables(tables)
    show_html(tables)

    return tables

def parse2():
    import ironpdf
    pdf = ironpdf.PdfDocument.FromFile(file)
    all_text = pdf.ExtractAllText()
    for row in all_text.split("\n"):
        print(row)

def parse3():
    import pdftotree

    page = pdftotree.parse(file, html_path='visualized.html', model_type=None, model_path=None, visualize=True)

    return page

if __name__ == '__main__':
    file = sys.argv[1]
    scale = 80
    if len(sys.argv) >= 3:
        scale = int(sys.argv[2])
    tables = parse1(file, line_scale=scale, split_text=True)
