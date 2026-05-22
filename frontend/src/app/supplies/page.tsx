"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Supply } from "@/lib/types";
import { 
  Package, Search, Plus, AlertTriangle, Edit3, Trash2, MapPin, 
  Layers, ChevronDown, Check, X, RefreshCw
} from "lucide-react";

export default function SuppliesPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedLocation, setSelectedLocation] = useState<string>("");
  
  // Modals/Forms State
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingSupply, setEditingSupply] = useState<Supply | null>(null);
  
  // New Supply form state
  const [newSupply, setNewSupply] = useState({
    name: "",
    category: "medication" as const,
    quantity_start: 100,
    quantity_used: 0,
    quantity_remaining: 100,
    expiration_date: "",
    lot_number: "",
    location: "venue_tent" as const,
    notes: "",
  });

  // Queries
  const { data: supplies, isLoading } = useQuery<Supply[]>({
    queryKey: ["supplies"],
    queryFn: () => apiFetch<Supply[]>("/supplies"),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (payload: typeof newSupply) => 
      apiFetch<Supply>("/supplies", {
        method: "POST",
        body: JSON.stringify({
          ...payload,
          event_id: "griztronics-2026", // hardcoded default
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supplies"] });
      setIsAddOpen(false);
      setNewSupply({
        name: "",
        category: "medication",
        quantity_start: 100,
        quantity_used: 0,
        quantity_remaining: 100,
        expiration_date: "",
        lot_number: "",
        location: "venue_tent",
        notes: "",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ supply_id, payload }: { supply_id: string; payload: Partial<Supply> }) => 
      apiFetch<Supply>(`/supplies/${supply_id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supplies"] });
      setEditingSupply(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (supply_id: string) => 
      apiFetch(`/supplies/${supply_id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supplies"] });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSupply.name.trim()) return;
    
    const remaining = Math.max(0, newSupply.quantity_start - newSupply.quantity_used);
    createMutation.mutate({
      ...newSupply,
      quantity_remaining: remaining,
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSupply) return;
    
    const remaining = Math.max(0, editingSupply.quantity_start - editingSupply.quantity_used);
    updateMutation.mutate({
      supply_id: editingSupply.supply_id,
      payload: {
        name: editingSupply.name,
        category: editingSupply.category,
        quantity_start: editingSupply.quantity_start,
        quantity_used: editingSupply.quantity_used,
        quantity_remaining: remaining,
        expiration_date: editingSupply.expiration_date,
        lot_number: editingSupply.lot_number,
        location: editingSupply.location,
        notes: editingSupply.notes,
      },
    });
  };

  const handleDelete = (supplyId: string) => {
    if (confirm("Are you sure you want to delete this inventory item?")) {
      deleteMutation.mutate(supplyId);
    }
  };

  const handleQuickAdjust = (supply: Supply, adjustment: number) => {
    const nextUsed = Math.max(0, supply.quantity_used + adjustment);
    const nextRemaining = Math.max(0, supply.quantity_start - nextUsed);
    updateMutation.mutate({
      supply_id: supply.supply_id,
      payload: {
        quantity_used: nextUsed,
        quantity_remaining: nextRemaining,
      },
    });
  };

  // Status checkers
  const isLowStock = (s: Supply) => {
    if (s.category === "narcan" && s.quantity_remaining < 20) return true;
    return s.quantity_remaining < (s.quantity_start * 0.3); // Under 30% remaining
  };

  // Filter supplies
  const filteredSupplies = supplies?.filter((s) => {
    const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (s.notes && s.notes.toLowerCase().includes(searchTerm.toLowerCase())) ||
                          (s.lot_number && s.lot_number.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory ? s.category === selectedCategory : true;
    const matchesLocation = selectedLocation ? s.location === selectedLocation : true;
    return matchesSearch && matchesCategory && matchesLocation;
  }) ?? [];

  return (
    <div className="space-y-6 max-w-6xl pb-16">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div className="flex items-center gap-3">
          <div className="bg-cyber-neonGreen/10 p-2 rounded-lg border border-cyber-neonGreen/30 text-cyber-neonGreen shadow-neonGreen">
            <Package size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide uppercase">Supplies Inventory</h1>
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
              Onsite pharmaceuticals, Narcan kits, and medical equipment
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsAddOpen(true)}
          className="flex items-center gap-1.5 bg-cyber-neonGreen text-black hover:bg-cyber-neonGreen/90 border border-cyber-neonGreen/50 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonGreen hover:scale-105"
        >
          <Plus size={14} />
          Add Supply Item
        </button>
      </div>

      {/* FILTER PANEL */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-zinc-950 border border-zinc-900 p-4 rounded-xl shadow-lg">
        {/* Search */}
        <div className="relative md:col-span-2">
          <input
            type="text"
            placeholder="Search supplies, lot #s, notes..."
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonGreen transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search size={14} className="absolute left-3 top-2.5 text-zinc-500" />
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="text-xs bg-zinc-900/50 border border-zinc-800 text-zinc-300 rounded-lg px-3 py-2 outline-none focus:border-cyber-neonGreen"
        >
          <option value="">All Categories</option>
          <option value="medication">Medication / Rx</option>
          <option value="narcan">Naloxone / Narcan</option>
          <option value="iv_fluid">IV Fluids / Saline</option>
          <option value="reagent">Reagent / Testing Kits</option>
          <option value="equipment">Medical Equipment</option>
          <option value="ppe">Personal Protective Equipment</option>
        </select>

        {/* Location Filter */}
        <select
          value={selectedLocation}
          onChange={(e) => setSelectedLocation(e.target.value)}
          className="text-xs bg-zinc-900/50 border border-zinc-800 text-zinc-300 rounded-lg px-3 py-2 outline-none focus:border-cyber-neonGreen"
        >
          <option value="">All Locations</option>
          <option value="venue_tent">Main Venue Medical Tent</option>
          <option value="campground">24/7 Campground Facility</option>
          <option value="rover_kit">Foot/ATV Rover Kits</option>
        </select>
      </div>

      {/* WARNINGS SUMMARY BANNER */}
      {supplies && supplies.filter(isLowStock).length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 text-amber-300 px-4 py-3 rounded-xl flex items-center gap-3 shadow-neonGreen/20">
          <AlertTriangle size={18} className="shrink-0" />
          <div className="text-xs">
            <span className="font-bold">Low Stock Warning:</span> {supplies.filter(isLowStock).length} medical item(s) are critically low (below 30% or under 20 Narcan boxes). Deploy rover kits carefully and coordinate with campground dispatch.
          </div>
        </div>
      )}

      {/* SUPPLIES MATRIX */}
      <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center text-zinc-500 text-sm">
            Loading supply matrix...
          </div>
        ) : filteredSupplies.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-900 text-left text-xs">
              <thead>
                <tr className="bg-zinc-950 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  <th className="px-5 py-4">Item Name / Lot</th>
                  <th className="px-5 py-4">Category</th>
                  <th className="px-5 py-4">Location</th>
                  <th className="px-5 py-4">Remaining / Start</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4 text-center">Quick Adjust</th>
                  <th className="px-5 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {filteredSupplies.map((s) => {
                  const lowStock = isLowStock(s);
                  const remainingPercent = s.quantity_start > 0 
                    ? Math.round((s.quantity_remaining / s.quantity_start) * 100) 
                    : 0;

                  return (
                    <tr
                      key={s.supply_id}
                      className="hover:bg-zinc-900/20 transition-colors"
                    >
                      <td className="px-5 py-4">
                        <span className="font-extrabold text-zinc-200 text-sm tracking-wide block">{s.name}</span>
                        <div className="flex gap-2 text-[10px] text-zinc-500 mt-1">
                          {s.lot_number && <span>Lot: <strong className="font-mono">{s.lot_number}</strong></span>}
                          {s.expiration_date && <span>Exp: <strong>{s.expiration_date}</strong></span>}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="px-2 py-0.5 rounded text-[9px] font-extrabold uppercase border bg-zinc-900 border-zinc-800 text-zinc-400 capitalize">
                          {s.category.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1 text-zinc-400">
                          <MapPin size={11} className="text-zinc-600" />
                          <span className="capitalize">{s.location.replace("_", " ")}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="space-y-1">
                          <div className="flex items-baseline gap-1 text-zinc-200">
                            <span className="font-black text-sm">{s.quantity_remaining}</span>
                            <span className="text-[10px] text-zinc-500">/ {s.quantity_start}</span>
                            <span className="text-[9px] text-zinc-500 ml-1">({remainingPercent}%)</span>
                          </div>
                          {/* Mini Progress Bar */}
                          <div className="w-24 h-1 bg-zinc-900 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${
                                lowStock ? "bg-amber-500" : "bg-cyber-neonGreen"
                              }`} 
                              style={{ width: `${Math.min(100, remainingPercent)}%` }} 
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
                          lowStock
                            ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                            : "bg-green-500/20 text-green-400 border-green-500/30"
                        }`}>
                          {lowStock ? "Low Stock" : "Sufficient"}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <div className="inline-flex rounded-lg border border-zinc-800 bg-zinc-900/30 overflow-hidden text-xs">
                          <button
                            onClick={() => handleQuickAdjust(s, -1)}
                            className="px-2.5 py-1 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors"
                            title="Decrement used"
                          >
                            +
                          </button>
                          <span className="px-2 py-1 text-zinc-300 bg-zinc-950 font-mono font-bold select-none border-x border-zinc-800">
                            {s.quantity_used}
                          </span>
                          <button
                            onClick={() => handleQuickAdjust(s, 1)}
                            className="px-2.5 py-1 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors"
                            title="Increment used"
                          >
                            -
                          </button>
                        </div>
                        <span className="block text-[9px] text-zinc-500 mt-1 uppercase font-bold tracking-wider">adjust used</span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingSupply(s)}
                            className="p-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 rounded transition-colors"
                            title="Edit details"
                          >
                            <Edit3 size={12} />
                          </button>
                          <button
                            onClick={() => handleDelete(s.supply_id)}
                            className="p-1.5 bg-zinc-900/50 hover:bg-red-500/10 text-zinc-500 hover:text-red-400 border border-zinc-900 hover:border-red-500/20 rounded transition-colors"
                            title="Delete item"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-64 flex flex-col items-center justify-center text-zinc-500 text-sm">
            No supply items matched your search filters
          </div>
        )}
      </div>

      {/* CREATE MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-900 max-w-md w-full rounded-2xl p-6 shadow-2xl space-y-4 animate-fade-in">
            <div className="flex justify-between items-center border-b border-zinc-900 pb-3">
              <h3 className="text-sm font-black uppercase tracking-wider text-white">Add Supply Item</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-zinc-500 hover:text-white transition-colors">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="block text-[10px] font-black uppercase text-zinc-500">Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Naloxone Nasal Spray 4mg"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                  value={newSupply.name}
                  onChange={(e) => setNewSupply({ ...newSupply, name: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Category</label>
                  <select
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={newSupply.category}
                    onChange={(e) => setNewSupply({ ...newSupply, category: e.target.value as any })}
                  >
                    <option value="medication">Medication / Rx</option>
                    <option value="narcan">Naloxone / Narcan</option>
                    <option value="iv_fluid">IV Fluids / Saline</option>
                    <option value="reagent">Reagent / Testing Kits</option>
                    <option value="equipment">Medical Equipment</option>
                    <option value="ppe">Personal Protective Equipment</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Location</label>
                  <select
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={newSupply.location}
                    onChange={(e) => setNewSupply({ ...newSupply, location: e.target.value as any })}
                  >
                    <option value="venue_tent">Main Venue Tent</option>
                    <option value="campground">Campground Facility</option>
                    <option value="rover_kit">Rover Kits</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Starting Quantity</label>
                  <input
                    type="number"
                    min="1"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={newSupply.quantity_start}
                    onChange={(e) => setNewSupply({ ...newSupply, quantity_start: parseInt(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Quantity Used</label>
                  <input
                    type="number"
                    min="0"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={newSupply.quantity_used}
                    onChange={(e) => setNewSupply({ ...newSupply, quantity_used: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Lot Number</label>
                  <input
                    type="text"
                    placeholder="e.g. Lot #188A"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen font-mono"
                    value={newSupply.lot_number}
                    onChange={(e) => setNewSupply({ ...newSupply, lot_number: e.target.value })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Expiration Date</label>
                  <input
                    type="text"
                    placeholder="YYYY-MM-DD"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={newSupply.expiration_date}
                    onChange={(e) => setNewSupply({ ...newSupply, expiration_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-black uppercase text-zinc-500">Notes / Details</label>
                <textarea
                  placeholder="Additional specs or shelf instructions..."
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen h-16 resize-none"
                  value={newSupply.notes}
                  onChange={(e) => setNewSupply({ ...newSupply, notes: e.target.value })}
                />
              </div>

              <div className="pt-3 border-t border-zinc-900 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 border border-zinc-800 text-zinc-400 hover:text-white rounded-lg transition-colors font-bold uppercase tracking-wider text-[10px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyber-neonGreen text-black font-bold uppercase rounded-lg shadow-neonGreen tracking-wider text-[10px]"
                >
                  Add Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editingSupply && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-900 max-w-md w-full rounded-2xl p-6 shadow-2xl space-y-4 animate-fade-in">
            <div className="flex justify-between items-center border-b border-zinc-900 pb-3">
              <h3 className="text-sm font-black uppercase tracking-wider text-white">Edit Supply Details</h3>
              <button onClick={() => setEditingSupply(null)} className="text-zinc-500 hover:text-white transition-colors">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="block text-[10px] font-black uppercase text-zinc-500">Item Name</label>
                <input
                  type="text"
                  required
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                  value={editingSupply.name}
                  onChange={(e) => setEditingSupply({ ...editingSupply, name: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Category</label>
                  <select
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={editingSupply.category}
                    onChange={(e) => setEditingSupply({ ...editingSupply, category: e.target.value as any })}
                  >
                    <option value="medication">Medication / Rx</option>
                    <option value="narcan">Naloxone / Narcan</option>
                    <option value="iv_fluid">IV Fluids / Saline</option>
                    <option value="reagent">Reagent / Testing Kits</option>
                    <option value="equipment">Medical Equipment</option>
                    <option value="ppe">Personal Protective Equipment</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Location</label>
                  <select
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={editingSupply.location}
                    onChange={(e) => setEditingSupply({ ...editingSupply, location: e.target.value as any })}
                  >
                    <option value="venue_tent">Main Venue Tent</option>
                    <option value="campground">Campground Facility</option>
                    <option value="rover_kit">Rover Kits</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Starting Quantity</label>
                  <input
                    type="number"
                    min="1"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={editingSupply.quantity_start}
                    onChange={(e) => setEditingSupply({ ...editingSupply, quantity_start: parseInt(e.target.value) || 0 })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Quantity Used</label>
                  <input
                    type="number"
                    min="0"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={editingSupply.quantity_used}
                    onChange={(e) => setEditingSupply({ ...editingSupply, quantity_used: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Lot Number</label>
                  <input
                    type="text"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen font-mono"
                    value={editingSupply.lot_number || ""}
                    onChange={(e) => setEditingSupply({ ...editingSupply, lot_number: e.target.value })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-[10px] font-black uppercase text-zinc-500">Expiration Date</label>
                  <input
                    type="text"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen"
                    value={editingSupply.expiration_date || ""}
                    onChange={(e) => setEditingSupply({ ...editingSupply, expiration_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-black uppercase text-zinc-500">Notes / Details</label>
                <textarea
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-150 focus:outline-none focus:border-cyber-neonGreen h-16 resize-none"
                  value={editingSupply.notes || ""}
                  onChange={(e) => setEditingSupply({ ...editingSupply, notes: e.target.value })}
                />
              </div>

              <div className="pt-3 border-t border-zinc-900 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingSupply(null)}
                  className="px-4 py-2 border border-zinc-800 text-zinc-400 hover:text-white rounded-lg transition-colors font-bold uppercase tracking-wider text-[10px]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-cyber-neonGreen text-black font-bold uppercase rounded-lg shadow-neonGreen tracking-wider text-[10px]"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
