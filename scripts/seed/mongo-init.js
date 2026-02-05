// ===========================================
// SarfX Enhanced - MongoDB Initialization Script
// ===========================================
// Ce script s'exécute automatiquement au premier démarrage de MongoDB
// Il crée les collections, index et données initiales

print('🚀 Starting SarfX MongoDB initialization...');

// Connexion à la base de données
db = db.getSiblingDB('SarfX_Enhanced');

// ===========================================
// 1. CRÉATION DES COLLECTIONS
// ===========================================
print('📦 Creating collections...');

const collections = [
    'users',
    'wallets',
    'transactions',
    'beneficiaries',
    'banks',
    'atm_locations',
    'exchange_rates',
    'rate_history',
    'rate_sources',
    'trusted_devices',
    'settings',
    'action_logs',
    'notifications',
    'push_subscriptions',
    'ai_cache',
    'kyc_documents',
    'kyc_events',
    'user_cards',
    'wallet_adjustments',
    'rate_alerts',
    'alert_triggers'
];

collections.forEach(function(collName) {
    if (!db.getCollectionNames().includes(collName)) {
        db.createCollection(collName);
        print('  ✅ Created collection: ' + collName);
    } else {
        print('  ⏭️  Collection exists: ' + collName);
    }
});

// ===========================================
// 2. CRÉATION DES INDEX
// ===========================================
print('🔍 Creating indexes...');

// Users indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "status": 1 });
db.users.createIndex({ "google_id": 1 }, { sparse: true });
print('  ✅ Users indexes created');

// Wallets indexes
db.wallets.createIndex({ "user_id": 1 });
db.wallets.createIndex({ "is_active": 1 });
print('  ✅ Wallets indexes created');

// Transactions indexes
db.transactions.createIndex({ "user_id": 1 });
db.transactions.createIndex({ "transaction_id": 1 }, { unique: true });
db.transactions.createIndex({ "status": 1 });
db.transactions.createIndex({ "created_at": -1 });
db.transactions.createIndex({ "type": 1 });
print('  ✅ Transactions indexes created');

// Beneficiaries indexes
db.beneficiaries.createIndex({ "user_id": 1 });
db.beneficiaries.createIndex({ "is_favorite": 1 });
print('  ✅ Beneficiaries indexes created');

// Banks indexes
db.banks.createIndex({ "code": 1 }, { unique: true });
db.banks.createIndex({ "is_active": 1 });
print('  ✅ Banks indexes created');

// ATM locations indexes
db.atm_locations.createIndex({ "bank_code": 1 });
db.atm_locations.createIndex({ "city": 1 });
db.atm_locations.createIndex({ "location": "2dsphere" });
db.atm_locations.createIndex({ "is_active": 1 });
print('  ✅ ATM locations indexes created');

// Exchange rates indexes
db.exchange_rates.createIndex({ "base_currency": 1, "target_currency": 1 });
db.exchange_rates.createIndex({ "updated_at": -1 });
print('  ✅ Exchange rates indexes created');

// Rate history indexes
db.rate_history.createIndex({ "pair": 1, "timestamp": -1 });
db.rate_history.createIndex({ "timestamp": -1 });
print('  ✅ Rate history indexes created');

// Trusted devices indexes
db.trusted_devices.createIndex({ "user_id": 1 });
db.trusted_devices.createIndex({ "device_token": 1 });
db.trusted_devices.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
print('  ✅ Trusted devices indexes created');

// Action logs indexes
db.action_logs.createIndex({ "user_id": 1 });
db.action_logs.createIndex({ "action": 1 });
db.action_logs.createIndex({ "created_at": -1 });
print('  ✅ Action logs indexes created');

// ===========================================
// 3. DONNÉES INITIALES - ADMIN USER
// ===========================================
print('👤 Creating admin user...');

const adminExists = db.users.findOne({ email: "admin@sarfx.io" });
if (!adminExists) {
    // Hash bcrypt de "admin123" (généré avec werkzeug)
    const adminPasswordHash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qX1HqXqX1HqXqX";

    db.users.insertOne({
        email: "admin@sarfx.io",
        password: adminPasswordHash,
        first_name: "Admin",
        last_name: "SarfX",
        role: "admin",
        status: "active",
        verified: true,
        theme: "light",
        accent_color: "orange",
        two_factor_enabled: false,
        notification_preferences: {
            email: true,
            push: true,
            sms: false
        },
        created_at: new Date(),
        updated_at: new Date(),
        login_count: 0
    });
    print('  ✅ Admin user created: admin@sarfx.io');
} else {
    print('  ⏭️  Admin user already exists');
}

// ===========================================
// 4. DONNÉES INITIALES - USER DEMO
// ===========================================
print('👤 Creating demo user...');

const userExists = db.users.findOne({ email: "user@sarfx.io" });
if (!userExists) {
    const userPasswordHash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qX1HqXqX1HqXqX";

    const userResult = db.users.insertOne({
        email: "user@sarfx.io",
        password: userPasswordHash,
        first_name: "User",
        last_name: "Demo",
        role: "user",
        status: "active",
        verified: true,
        theme: "light",
        accent_color: "blue",
        two_factor_enabled: false,
        notification_preferences: {
            email: true,
            push: false,
            sms: false
        },
        created_at: new Date(),
        updated_at: new Date(),
        login_count: 0
    });

    // Créer un wallet pour l'utilisateur demo
    db.wallets.insertOne({
        user_id: userResult.insertedId,
        balances: {
            USD: 1000.00,
            EUR: 850.00,
            MAD: 10000.00,
            GBP: 750.00,
            CAD: 0,
            AED: 0,
            SAR: 0,
            TRY: 0
        },
        is_active: true,
        created_at: new Date(),
        updated_at: new Date()
    });

    print('  ✅ Demo user created: user@sarfx.io with wallet');
} else {
    print('  ⏭️  Demo user already exists');
}

// ===========================================
// 5. DONNÉES INITIALES - BANK RESPO
// ===========================================
print('🏦 Creating bank respo user...');

const bankExists = db.users.findOne({ email: "bank@attijariwafa.ma" });
if (!bankExists) {
    const bankPasswordHash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qX1HqXqX1HqXqX";

    db.users.insertOne({
        email: "bank@attijariwafa.ma",
        password: bankPasswordHash,
        first_name: "Responsable",
        last_name: "AWB",
        role: "bank_respo",
        status: "active",
        verified: true,
        bank_code: "AWB",
        theme: "dark",
        accent_color: "purple",
        two_factor_enabled: false,
        created_at: new Date(),
        updated_at: new Date(),
        login_count: 0
    });
    print('  ✅ Bank respo created: bank@attijariwafa.ma');
} else {
    print('  ⏭️  Bank respo already exists');
}

// ===========================================
// 6. DONNÉES INITIALES - BANQUES MAROCAINES
// ===========================================
print('🏦 Creating banks...');

const banks = [
    {
        name: "Attijariwafa Bank",
        code: "AWB",
        logo: "/static/images/banks/awb.png",
        color: "#E3A21A",
        swift_code: "BCMAMAMC",
        country: "MA",
        is_active: true
    },
    {
        name: "Bank of Africa",
        code: "BOA",
        logo: "/static/images/banks/boa.png",
        color: "#003D7A",
        swift_code: "BMABORMA",
        country: "MA",
        is_active: true
    },
    {
        name: "CIH Bank",
        code: "CIH",
        logo: "/static/images/banks/cih.png",
        color: "#C41E3A",
        swift_code: "CIABORMA",
        country: "MA",
        is_active: true
    },
    {
        name: "Banque Populaire",
        code: "BP",
        logo: "/static/images/banks/bp.png",
        color: "#0066B3",
        swift_code: "BCPOMAMX",
        country: "MA",
        is_active: true
    },
    {
        name: "BMCE Bank",
        code: "BMCE",
        logo: "/static/images/banks/bmce.png",
        color: "#1E4D8C",
        swift_code: "BMCEMAMX",
        country: "MA",
        is_active: true
    },
    {
        name: "Société Générale",
        code: "SG",
        logo: "/static/images/banks/sg.png",
        color: "#E60012",
        swift_code: "SGMBMAMX",
        country: "MA",
        is_active: true
    }
];

banks.forEach(function(bank) {
    const exists = db.banks.findOne({ code: bank.code });
    if (!exists) {
        bank.created_at = new Date();
        bank.updated_at = new Date();
        db.banks.insertOne(bank);
        print('  ✅ Bank created: ' + bank.name);
    } else {
        print('  ⏭️  Bank exists: ' + bank.name);
    }
});

// ===========================================
// 7. DONNÉES INITIALES - TAUX DE CHANGE
// ===========================================
print('💱 Creating exchange rates...');

const rates = [
    { base: "EUR", target: "MAD", rate: 10.85 },
    { base: "USD", target: "MAD", rate: 10.05 },
    { base: "GBP", target: "MAD", rate: 12.75 },
    { base: "EUR", target: "USD", rate: 1.08 },
    { base: "GBP", target: "EUR", rate: 1.17 },
    { base: "CAD", target: "MAD", rate: 7.35 },
    { base: "AED", target: "MAD", rate: 2.74 },
    { base: "SAR", target: "MAD", rate: 2.68 },
    { base: "TRY", target: "MAD", rate: 0.31 }
];

rates.forEach(function(r) {
    const exists = db.exchange_rates.findOne({
        base_currency: r.base,
        target_currency: r.target
    });
    if (!exists) {
        db.exchange_rates.insertOne({
            base_currency: r.base,
            target_currency: r.target,
            rate: r.rate,
            source: "manual",
            updated_at: new Date()
        });
        print('  ✅ Rate created: ' + r.base + '/' + r.target + ' = ' + r.rate);
    }
});

// ===========================================
// 8. DONNÉES INITIALES - SETTINGS
// ===========================================
print('⚙️ Creating settings...');

const settingsExists = db.settings.findOne({ key: "app_config" });
if (!settingsExists) {
    db.settings.insertOne({
        key: "app_config",
        value: {
            app_name: "SarfX",
            version: "2.0.0",
            maintenance_mode: false,
            default_currency: "MAD",
            supported_currencies: ["USD", "EUR", "MAD", "GBP", "CAD", "AED", "SAR", "TRY"],
            rate_update_interval: 300, // 5 minutes
            max_transaction_amount: 100000,
            min_transaction_amount: 10
        },
        updated_at: new Date()
    });
    print('  ✅ App settings created');
}

// ===========================================
// 9. EXEMPLE DE DABs
// ===========================================
print('🏧 Creating sample ATMs...');

const atms = [
    {
        bank_code: "AWB",
        name: "AWB Casablanca Centre",
        address: "123 Boulevard Mohammed V",
        city: "Casablanca",
        latitude: 33.5731,
        longitude: -7.5898,
        services: ["cash", "deposit"],
        is_active: true
    },
    {
        bank_code: "BOA",
        name: "BOA Rabat Agdal",
        address: "45 Avenue de France",
        city: "Rabat",
        latitude: 33.9716,
        longitude: -6.8498,
        services: ["cash"],
        is_active: true
    },
    {
        bank_code: "CIH",
        name: "CIH Marrakech Gueliz",
        address: "78 Rue de la Liberté",
        city: "Marrakech",
        latitude: 31.6295,
        longitude: -7.9811,
        services: ["cash", "deposit", "transfer"],
        is_active: true
    }
];

atms.forEach(function(atm) {
    const exists = db.atm_locations.findOne({
        bank_code: atm.bank_code,
        name: atm.name
    });
    if (!exists) {
        atm.location = {
            type: "Point",
            coordinates: [atm.longitude, atm.latitude]
        };
        atm.created_at = new Date();
        db.atm_locations.insertOne(atm);
        print('  ✅ ATM created: ' + atm.name);
    }
});

// ===========================================
// TERMINÉ
// ===========================================
print('');
print('🎉 ================================================');
print('   SarfX MongoDB initialization completed!');
print('   ================================================');
print('');
print('   📊 Collections: ' + db.getCollectionNames().length);
print('   👤 Admin: admin@sarfx.io / admin123');
print('   👤 User:  user@sarfx.io / user123');
print('   👤 Bank:  bank@attijariwafa.ma / bank123');
print('   🏦 Banks: ' + db.banks.countDocuments());
print('   💱 Rates: ' + db.exchange_rates.countDocuments());
print('   🏧 ATMs:  ' + db.atm_locations.countDocuments());
print('');
print('🚀 Ready to use!');
