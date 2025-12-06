# How to run locally

- Make sure docker volume oblivionis exists for Postgres
- Make sure postgres has databases `oblivionis` and `storage_v2`
- Run `build-run.sh` in backend to fire up backend
- Run `npm run dev` to fire up frontend
    - Maybe edit `vite.config.ts` depending on where you wanna proxy api calls
