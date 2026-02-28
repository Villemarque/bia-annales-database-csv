import type { LocalStorageKey } from '$lib/types';

const prefix = 'annales-bia-csv';

// TODO, switch to `idb` package?
export type IDbValue = Blob | string | ArrayBuffer | Uint8Array | string[] | number | object;

// bump version when touching this
const storeKeys = ['log', 'attempt', 'session'] as const;
type StoreKeys = (typeof storeKeys)[number];

export class Db {
	private inner: IDBDatabase;
	stores: Record<StoreKeys, Store>;

	constructor(inner: IDBDatabase, stores: Record<StoreKeys, Store>) {
		this.inner = inner;
		this.stores = stores;
	}

	static async open(): Promise<Db> {
		const openReq = indexedDB.open(prefix, 2);
		return new Promise<Db>((resolve) => {
			openReq.onupgradeneeded = () => {
				const db = openReq.result;
				// create all stores
				for (const storeKey of storeKeys) {
					if (!db.objectStoreNames.contains(storeKey)) {
						console.log(`Creating object store: ${storeKey}`);
						db.createObjectStore(storeKey, { keyPath: 'id' });
					}
				}
			};
			openReq.onerror = (event: any) => console.error(`DB open error: ${JSON.stringify(event)}`);
			openReq.onblocked = function () {
				// this event shouldn't trigger if we handle onversionchange correctly
				const blocked = 'Database is blocked, close all other tabs of this page';
				console.error(blocked);
				alert(blocked);
			};
			openReq.onsuccess = function () {
				const db = openReq.result;

				db.onversionchange = function () {
					db.close();
					const outdated = 'Database is outdated, please reload the page.';
					console.error(outdated);
					alert(outdated);
				};
				const stores = {
					log: new Store(db, 'log'),
					attempt: new Store(db, 'attempt'),
					session: new Store(db, 'session')
				};
				resolve(new Db(db, stores));
			};
		});
	}

	// delete the current Db (IDB + Localstorage)
	async clearDb(): Promise<void> {
		const closeDb = this.inner;
		closeDb.close();
		const deleteReq = indexedDB.deleteDatabase(prefix);
		localStorage.clear();
		return new Promise<void>((resolve, reject) => {
			deleteReq.onsuccess = () => {
				resolve();
			};
			deleteReq.onerror = (event: any) => reject(new Error(`Failed to delete IndexedDB: ${event}`));
			deleteReq.onblocked = () => {
				const blocked = 'Database deletion is blocked, close all other tabs of this page';
				console.error(blocked);
				alert(blocked);
			};
		});
	}

	static getLocalStorage(key: LocalStorageKey): string | null {
		const value = window.localStorage.getItem(`${prefix}-${key}`);
		return value;
	}

	static setLocalSorage(key: LocalStorageKey, value: string) {
		// console.log(`localStorage set: key {${key}} value {${value}}`);
		window.localStorage.setItem(`${prefix}-${key}`, value);
	}
}

function promise<V>(f: () => IDBRequest) {
	return new Promise<V>((resolve, reject) => {
		const res = f();
		res.onsuccess = (e: Event) => {
			resolve((e.target as IDBRequest).result);
		};
		res.onerror = (e: Event) => reject((e.target as IDBRequest).result);
	});
}

// IDB store, based on lila/ui/lib/src/objectStorage.ts, AGPL
export class Store {
	private db: IDBDatabase;
	private storeKey: StoreKeys;

	constructor(db: IDBDatabase, storeKey: StoreKeys) {
		this.db = db;
		this.storeKey = storeKey;
	}

	objectStore = (mode: IDBTransactionMode) => {
		return this.db.transaction(this.storeKey, mode).objectStore(this.storeKey);
	};

	async get<T extends IDbValue>(key: IDBValidKey): Promise<T | null> {
		// @ts-ignore
		return promise(() => this.objectStore('readonly').get(key));
	}

	// ArrayBuffer, Blob, File, and typed arrays like Uint8Array
	async put(key: IDbValue, value: IDbValue): Promise<void> {
		return promise(() => this.objectStore('readwrite').put({ id: key, data: value }));
	}

	async clear(): Promise<void> {
		return promise(() => this.objectStore('readwrite').clear());
	}

	async list(): Promise<IDBValidKey[]> {
		return promise(() => this.objectStore('readonly').getAllKeys());
	}

	async getMany<T extends IDbValue>(keys?: IDBKeyRange): Promise<(T | null)[]> {
		return promise(() => this.objectStore('readonly').getAll(keys));
	}

	async remove(key: IDBValidKey | IDBKeyRange): Promise<void> {
		return promise(() => this.objectStore('readwrite').delete(key));
	}
}
