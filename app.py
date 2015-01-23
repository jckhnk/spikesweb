import os, sys
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)


import matplotlib.pyplot as plt
import seaborn as sns
import mpld3

import dataset
import pandas as pd
import sqlite3


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        column_names = ' '.join(db[tablename].columns)
        self.render('index.html', columns=column_names)

class PlotPageHandler(tornado.web.RequestHandler):
    def post(self):

        # column = self.get_argument('column')
        # operator = self.get_argument('operator')
        # value = self.get_argument('value')
        # query = "{} {} {}".format(column, operator, value)

        query = self.get_argument('query')
        x = self.get_argument('x')
        y = self.get_argument('y')
        query_str = 'SELECT * FROM {} WHERE ({})'.format(tablename, query)

        # result_str = ""
        # a, b = [], []
        # for i, item in enumerate(result):
        #     if i == 0:
        #         result_str += " ".join(item.keys())+'\n'
        #     a.append(item[x])
        #     b.append(item[y])
        #     values_str = [str(j) for j in item.values()]
        #     result_str += " ".join(values_str)+'\n'

        if plot_type == 'basic':
            result = db.query(query_str)
            points = [(i[x], i[y]) for i in result]
            a, b = zip(*points)
            fig, ax = plt.subplots()
            fig.set_size_inches(8, 8)
            ax.plot(a, b, 'ob', ms=10, alpha=0.1)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
        elif plot_type == 'experimental':
            df = pd.read_sql(query_str, conn)
            if '-' in x:
                x = df[x.split('-')[0]] - df[x.split('-')[1]]
            else:
                x = df[x]
            if '-' in y:
                y = df[y.split('-')[0]] - df[y.split('-')[1]]
            else:
                y = df[y]
            # fig = sns.jointplot(x, y, stat_func=None).fig
            fig = sns.jointplot(x, y, stat_func=None, size=8).fig
        plot_html = mpld3.fig_to_html(fig)
        self.finish(plot_html)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[(r'/', IndexHandler), (r'/plot', PlotPageHandler)],
        template_path=os.path.join(os.path.dirname(__file__), "templates")
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    if len(sys.argv) < 2:
        tablename = 'd5883'
        plot_type = 'basic'
    elif len(sys.argv) == 3:
        tablename = sys.argv[1]
        plot_type = sys.argv[2]
    else:
        print "Usage: app.py tablename plot_type"
    db = dataset.connect('sqlite:///test.db')
    conn = sqlite3.connect('test.db')
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "\nGoodbye"
        conn.close()