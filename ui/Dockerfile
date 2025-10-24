FROM node:18-alpine

WORKDIR /app

# Install production dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy the rest of the UI source
COPY . .

# Build the Next.js application for production
RUN npm run build

EXPOSE 3000

# Start the production server
CMD ["npm", "start"]
