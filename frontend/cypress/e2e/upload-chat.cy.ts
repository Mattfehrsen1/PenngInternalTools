describe('Upload and Chat Flow', () => {
  beforeEach(() => {
    // Login first
    cy.visit('/login');
    cy.get('input[id="username"]').type('demo');
    cy.get('input[id="password"]').type('demo123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/chat');
  });

  it('should upload a text and chat with it', () => {
    // Switch to text mode
    cy.contains('button', 'Paste Text').click();
    
    // Enter text
    cy.get('textarea').type('Alex Hormozi teaches the value stack formula: Dream Outcome x Perceived Likelihood of Achievement / (Time Delay x Effort and Sacrifice) = Value');
    
    // Enter name
    cy.get('input[id="name"]').type('Alex Hormozi Value Stack');
    
    // Submit
    cy.contains('button', 'Create Clone').click();
    
    // Wait for processing
    cy.contains('Processing your text...', { timeout: 10000 });
    cy.contains('Great! Your clone has been created', { timeout: 30000 });
    
    // Ask a question
    cy.get('input[placeholder="Ask a question..."]').type('What is the value stack formula?');
    cy.get('button[aria-label="Send"]').click();
    
    // Check response
    cy.contains('Dream Outcome', { timeout: 10000 });
    cy.contains('Sources:', { timeout: 5000 });
  });

  it('should handle PDF upload', () => {
    // File upload would require a test PDF
    cy.get('input[type="file"]').should('exist');
    cy.contains('Drag & drop a PDF here');
  });

  it('should switch between models', () => {
    // Create a clone first (using text for speed)
    cy.contains('button', 'Paste Text').click();
    cy.get('textarea').type('Test content');
    cy.get('input[id="name"]').type('Test Clone');
    cy.contains('button', 'Create Clone').click();
    cy.contains('Great! Your clone has been created', { timeout: 30000 });
    
    // Check model selector
    cy.get('[role="combobox"]').click();
    cy.contains('GPT-4o').click();
    cy.get('[role="combobox"]').should('contain', 'GPT-4o');
    
    cy.get('[role="combobox"]').click();
    cy.contains('Claude 3').click();
    cy.get('[role="combobox"]').should('contain', 'Claude 3');
  });
});
