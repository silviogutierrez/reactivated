import app from './server/app';

app.listen({node: 3000, django: 8000}, () => console.log('Example app listening on port 3000!'))
