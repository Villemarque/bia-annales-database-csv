import { Db } from './db';

let theGlobalDb: Db;
let init: (db: Db) => void;

export const getDb = new Promise<Db>((resolve) => {
	init = (db: Db) => {
		resolve(db);
	};
});

export const initDb = async (): Promise<void> => {
	theGlobalDb = await Db.open();
	init(theGlobalDb);
};
