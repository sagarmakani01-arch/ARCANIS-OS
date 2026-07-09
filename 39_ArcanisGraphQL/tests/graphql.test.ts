import { describe, it, expect, beforeEach } from 'vitest';
import { GraphQLGateway } from '../src/graphql.js';

describe('GraphQLGateway', () => {
  let gql: GraphQLGateway;
  beforeEach(() => { gql = new GraphQLGateway({ depthLimit: 5 }); });

  describe('schema', () => {
    it('should add types and queries', () => {
      gql.addType({ name: 'User', fields: [{ name: 'id', type: 'ID' }, { name: 'name', type: 'String' }] });
      gql.addQuery({ name: 'user', returnType: 'User', args: [{ name: 'id', type: 'ID', required: true }], resolver: 'getUser' });
      gql.addMutation({ name: 'createUser', returnType: 'User', args: [{ name: 'name', type: 'String', required: true }], resolver: 'createUser' });
      expect(gql.introspect().types.length).toBe(1);
      expect(gql.introspect().queries.length).toBe(1);
      expect(gql.introspect().mutations.length).toBe(1);
    });
  });

  describe('execution', () => {
    it('should execute query with resolver', async () => {
      gql.addQuery({ name: 'hello', returnType: 'String', resolver: 'hello' });
      gql.registerResolver('Query', 'hello', () => 'world');
      const res = await gql.execute({ query: '{ hello }' });
      expect(res.data).toBe('world');
    });
    it('should return error for missing resolver', async () => {
      const res = await gql.execute({ query: '{ missing }' });
      expect(res.errors).toBeDefined();
    });
    it('should enforce depth limit', async () => {
      const res = await gql.execute({ query: '{ a { b { c { d { e { f } } } } } }' });
      expect(res.errors?.[0].message).toContain('depth');
    });
  });

  describe('persisted queries', () => {
    it('should store and retrieve persisted queries', () => {
      gql.persistQuery('q1', '{ user { name } }');
      expect(gql.getPersistedQuery('q1')).toBe('{ user { name } }');
    });
  });

  describe('introspection', () => {
    it('should generate schema string', () => {
      gql.addQuery({ name: 'users', returnType: 'User', resolver: 'getUsers' });
      const str = gql.generateSchemaString();
      expect(str).toContain('type Query');
      expect(str).toContain('users');
    });
  });

  describe('query logs', () => {
    it('should track query execution', async () => {
      gql.addQuery({ name: 'hello', returnType: 'String', resolver: 'hello' });
      gql.registerResolver('Query', 'hello', () => 'world');
      await gql.execute({ query: '{ hello }' });
      expect(gql.getQueryLogs().length).toBe(1);
    });
  });

  describe('measureDepth', () => {
    it('should measure query depth', () => {
      expect(gql.measureDepth('{ a { b } }')).toBe(2);
      expect(gql.measureDepth('{ a { b { c { d } } } }')).toBe(4);
      expect(gql.measureDepth('{ a }')).toBe(1);
    });
  });
});
