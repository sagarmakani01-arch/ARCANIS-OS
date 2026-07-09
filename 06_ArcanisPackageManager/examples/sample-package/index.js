'use strict';

function greet(name) {
  return `Hello, ${name}! Welcome to Arcanis.`;
}

function add(a, b) {
  return a + b;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = { greet, add, delay };
