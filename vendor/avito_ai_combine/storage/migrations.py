TABLES=['avito_accounts','oauth_credentials','account_capabilities','webhook_subscriptions','chats','messages','message_events','leads','lead_events','lead_notes','lead_tasks','lead_tags','listings','listing_snapshots','listing_stats_daily','promotion_orders','autoload_runs','autoload_item_results','reviews','calls','call_transcripts','automation_rules','automation_runs','approval_requests','ai_profiles','knowledge_documents','ai_runs','audit_log','jobs']
class MigrationRunner:
    @staticmethod
    def apply(db):
        db.integrity_check()
        with db.transaction() as c:
            c.execute('create table if not exists schema_version(version integer primary key)')
            for t in TABLES: c.execute(f'create table if not exists {t}(id integer primary key, external_id text, account_id text, data text, created_at text default current_timestamp)')
            c.executescript('''
            create unique index if not exists ux_events_external on message_events(external_id);
            create unique index if not exists ux_chats_external on chats(external_id,account_id);
            create unique index if not exists ux_messages_external on messages(external_id,account_id);
            create unique index if not exists ux_leads_external on leads(external_id,account_id);
            create index if not exists ix_messages_account_created on messages(account_id,created_at);
            create index if not exists ix_leads_account_created on leads(account_id,created_at);
            ''')
            c.execute('insert or ignore into schema_version(version) values (1)')
        return 1
