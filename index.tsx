import app from './server/app';

app.listen({port: 3000, django: 8000}, () => console.log('Example app listening on port 3000!'))