import type { Express } from "express";
import type { Server } from "node:http";
export async function registerRoutes(httpServer: Server, _app: Express): Promise<Server> {
  return httpServer;
}
