import webpack from 'webpack';
import path from 'path';

export default {
    mode: 'development',
    entry: './client/app.tsx',
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/
            },
        ],
    },
    resolve: {
        extensions: [ '.tsx', '.ts', '.js' ],
        symlinks: false,
    },
    output: {
        filename: 'dist/bundle.js',
        publicPath: '/media/',
    },
	serve: {
        devMiddleware: {
            publicPath: '/media/',
        },
	},

    devServer: {
        // disableHostCheck: true,
        // port: (DEBUG_PORT + 100),
        // host: process.env.HOSTNAME || '0.0.0.0',
        // public: '192.168.1.67:8080',
        hot: true,
        inline: true,
        // progress: true,

        // Display only errors to reduce the amount of output.
        // stats: 'errors-only',
        // https: isProductionBuild ? null : {
        //     cert: fs.readFileSync(path.resolve(__dirname, 'cert.crt')),
        //     key: fs.readFileSync(path.resolve(__dirname, 'cert.key')),
        // },
        // cert: '/Users/silviogutierrez/Sites/django/master.joyapp.com/src/master.joyapp.com/cert.crt',
        // key: '/Users/silviogutierrez/Sites/django/master.joyapp.com/src/master.joyapp.com/cert.key',
        proxy: {
            '**': {
                target: 'http://localhost:3001',
                // secure: false,
                // Lie and fake the https in our referer so that we can run
                // webpack without SSL, but run jk
                /*
                onProxyReq: function(proxyReq, req) {
                    var referer = req.headers['referer'];
                    proxyReq.setHeader('referer', referer.replace('http:', 'https:'));
                },
                */
            },
        },
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin(),
    ],
};
