import { useState, useEffect } from 'react'
import gameAPI, { Equipment, ShopInventory, GladiatorWithEquipment } from '../services/gameAPI'
import styles from './EquipmentManager.module.css'

interface EquipmentManagerProps {
  gladiator: GladiatorWithEquipment
  onGladiatorUpdate: (gladiator: GladiatorWithEquipment) => void
  onClose: () => void
  view: 'inventory' | 'shop'
}

type ShopCategory = 'all' | 'weapons'
type WeaponSubcategory = 'all' | 'axe' | 'sword' | 'hammer' | 'staff' | 'ranged' | 'stabbing' | 'chain'

const weaponSubcategoryOptions: { key: WeaponSubcategory; label: string }[] = [
  { key: 'all', label: 'All Weapons' },
  { key: 'axe', label: 'Axes' },
  { key: 'sword', label: 'Swords' },
  { key: 'hammer', label: 'Hammers' },
  { key: 'staff', label: 'Staves' },
  { key: 'ranged', label: 'Ranged Weapons' },
  { key: 'stabbing', label: 'Stabbing Weapons' },
  { key: 'chain', label: 'Chain Weapons' },
]

export function EquipmentManager({
  gladiator,
  onGladiatorUpdate,
  onClose,
  view,
}: EquipmentManagerProps) {
  const [shopInventory, setShopInventory] = useState<ShopInventory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ShopCategory>('weapons')
  const [selectedWeaponSubcategory, setSelectedWeaponSubcategory] = useState<WeaponSubcategory>('all')

  const equipmentSlots = [
    { key: 'weapon', label: 'Weapon' },
    { key: 'offhand', label: 'Offhand' },
    { key: 'head', label: 'Head' },
    { key: 'shoulders', label: 'Shoulders' },
    { key: 'chest', label: 'Chest' },
    { key: 'hands', label: 'Hands' },
    { key: 'legs', label: 'Legs' },
    { key: 'feet', label: 'Feet' },
    { key: 'cape', label: 'Cape' },
    { key: 'neck', label: 'Neck' },
    { key: 'ring', label: 'Ring' },
    { key: 'amulet', label: 'Amulet' },
    { key: 'bracers', label: 'Bracers' },
    { key: 'ornament', label: 'Ornament' },
  ]

  useEffect(() => {
    if (view === 'shop') {
      loadShopInventory()
    }
  }, [view])

  const loadShopInventory = async () => {
    setLoading(true)
    setError('')
    try {
      const inventory = await gameAPI.getShopInventory()
      setShopInventory(inventory)
    } catch (err) {
      setError('Failed to load shop inventory')
    } finally {
      setLoading(false)
    }
  }

  const handleEquipItem = async (equipmentId: number, slot: string) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.equipItem({ equipment_id: equipmentId, slot })
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
    } catch (err) {
      setError('Failed to equip item')
    } finally {
      setLoading(false)
    }
  }

  const handleUnequipItem = async (slot: string) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.unequipItem(slot)
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
    } catch (err) {
      setError('Failed to unequip item')
    } finally {
      setLoading(false)
    }
  }

  const handlePurchaseItem = async (equipmentId: number) => {
    setLoading(true)
    setError('')
    try {
      await gameAPI.purchaseEquipment(equipmentId)
      const updatedGladiator = await gameAPI.getGladiatorWithEquipment()
      onGladiatorUpdate(updatedGladiator)
      await loadShopInventory()
    } catch (err) {
      setError('Failed to purchase item')
    } finally {
      setLoading(false)
    }
  }

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common':
        return '#888'
      case 'rare':
        return '#0066cc'
      case 'epic':
        return '#9933cc'
      case 'legendary':
        return '#ff9900'
      default:
        return '#888'
    }
  }

  const getStatBonuses = (equipment: Equipment) => {
    const bonuses = []
    if (equipment.strength_bonus > 0) bonuses.push(`+${equipment.strength_bonus} Strength`)
    if (equipment.vitality_bonus > 0) bonuses.push(`+${equipment.vitality_bonus} Vitality`)
    if (equipment.stamina_bonus > 0) bonuses.push(`+${equipment.stamina_bonus} Stamina`)
    if (equipment.dodge_bonus > 0) bonuses.push(`+${equipment.dodge_bonus} Dodge`)
    if (equipment.initiative_bonus > 0) bonuses.push(`+${equipment.initiative_bonus} Initiative`)
    if (equipment.weaponskill_bonus > 0) bonuses.push(`+${equipment.weaponskill_bonus} Weaponskill`)
    return bonuses.join(', ')
  }

  const getRequirementState = (item: Equipment) => {
    const goldMissing = gladiator.gold < item.value
    return {
      goldMissing,
      canBuy: !goldMissing,
    }
  }

  const normalizeWeaponSubtype = (value?: string | null): WeaponSubcategory | null => {
    const raw = (value || '').trim().toLowerCase()
    if (!raw) return null

    switch (raw) {
      case 'axe':
      case 'axes':
        return 'axe'
      case 'sword':
      case 'swords':
        return 'sword'
      case 'hammer':
      case 'hammers':
        return 'hammer'
      case 'staff':
      case 'staves':
      case 'staffs':
        return 'staff'
      case 'ranged':
      case 'range':
      case 'ranged weapon':
      case 'ranged weapons':
        return 'ranged'
      case 'stabbing':
      case 'stabbing weapon':
      case 'stabbing weapons':
        return 'stabbing'
      case 'chain':
      case 'chain weapon':
      case 'chain weapons':
        return 'chain'
      default:
        return null
    }
  }

  const formatWeaponSubtype = (value?: string | null): string | null => {
    const normalized = normalizeWeaponSubtype(value)
    switch (normalized) {
      case 'axe':
        return 'axe'
      case 'sword':
        return 'sword'
      case 'hammer':
        return 'hammer'
      case 'staff':
        return 'staff'
      case 'ranged':
        return 'ranged'
      case 'stabbing':
        return 'stabbing'
      case 'chain':
        return 'chain'
      default:
        return null
    }
  }

  const filteredShopItems = (() => {
    if (!shopInventory) return []

    let items = shopInventory.available_items
    if (selectedCategory === 'weapons') {
      items = items.filter((item) => item.item_type === 'weapon')
      if (selectedWeaponSubcategory !== 'all') {
        items = items.filter(
          (item) => normalizeWeaponSubtype(item.weapon_subtype) === selectedWeaponSubcategory,
        )
      }
    }

    return items
  })()

  const headerTitle = view === 'shop' ? 'Store' : 'Equipment'

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>{headerTitle}</h2>
          <div className={styles.goldDisplay}>
            Gold: {gladiator.gold}
          </div>
        </div>
        <button className={styles.closeButton} onClick={onClose}>
          Close
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {view === 'inventory' && (
        <div className={styles.inventorySection}>
          <div className={styles.equippedItems}>
            <h3>Equipped Items</h3>
            <div className={styles.slotsGrid}>
              {equipmentSlots.map((slot) => {
                const equippedItem = gladiator.equipped_items?.[slot.key]
                return (
                  <div key={slot.key} className={styles.slot}>
                    <div className={styles.slotName}>{slot.label}</div>
                    {equippedItem ? (
                      <div className={styles.equippedItem}>
                        <div className={styles.itemName} style={{ color: getRarityColor(equippedItem.rarity) }}>
                          {equippedItem.name}
                        </div>
                        <div className={styles.itemStats}>{getStatBonuses(equippedItem)}</div>
                        <button
                          className={styles.unequipButton}
                          onClick={() => handleUnequipItem(slot.key)}
                          disabled={loading}
                        >
                          Unequip
                        </button>
                      </div>
                    ) : (
                      <div className={styles.emptySlot}>Empty</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className={styles.inventory}>
            <h3>Inventory</h3>
            <div className={styles.inventoryGrid}>
              {gladiator.inventory?.filter((item) => !item.is_equipped).map((item) => (
                <div key={item.id} className={styles.inventoryItem}>
                  <div className={styles.itemName} style={{ color: getRarityColor(item.equipment.rarity) }}>
                    {item.equipment.name}
                  </div>
                  <div className={styles.itemType}>{item.equipment.slot}</div>
                  <div className={styles.itemStats}>{getStatBonuses(item.equipment)}</div>
                  <button
                    className={styles.equipButton}
                    onClick={() => handleEquipItem(item.equipment.id, item.equipment.slot)}
                    disabled={loading}
                  >
                    Equip
                  </button>
                </div>
              ))}
              {(!gladiator.inventory || gladiator.inventory.filter((item) => !item.is_equipped).length === 0) && (
                <div className={styles.emptyInventory}>No items in inventory</div>
              )}
            </div>
          </div>
        </div>
      )}

      {view === 'shop' && (
        <div className={styles.shopSection}>
          <h3>Store</h3>
          <div className={styles.categoryFilters}>
            <button
              className={`${styles.filterButton} ${selectedCategory === 'all' ? styles.filterButtonActive : ''}`}
              onClick={() => setSelectedCategory('all')}
            >
              All
            </button>
            <button
              className={`${styles.filterButton} ${selectedCategory === 'weapons' ? styles.filterButtonActive : ''}`}
              onClick={() => setSelectedCategory('weapons')}
            >
              Weapons
            </button>
          </div>

          {selectedCategory === 'weapons' && (
            <div className={styles.subcategoryFilters}>
              {weaponSubcategoryOptions.map((option) => (
                <button
                  key={option.key}
                  className={`${styles.filterButton} ${selectedWeaponSubcategory === option.key ? styles.filterButtonActive : ''}`}
                  onClick={() => setSelectedWeaponSubcategory(option.key)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}

          {loading ? (
            <div className={styles.loading}>Loading shop inventory...</div>
          ) : shopInventory ? (
            <div className={styles.shopGrid}>
              {filteredShopItems.map((item) => {
                const req = getRequirementState(item)
                const weaponSubtype = formatWeaponSubtype(item.weapon_subtype)
                const itemTypeLabel = item.item_type === 'weapon' && weaponSubtype
                  ? `${item.item_type} / ${weaponSubtype}`
                  : item.item_type
                return (
                  <div
                    key={item.id}
                    className={`${styles.shopItem} ${!req.canBuy ? styles.shopItemLocked : ''}`}
                  >
                    <div className={styles.itemHeader}>
                      <div className={styles.itemName} style={{ color: getRarityColor(item.rarity) }}>
                        {item.name}
                      </div>
                      <div className={styles.itemLevel}>Level {item.level_requirement}</div>
                    </div>
                    <div className={styles.itemType}>{item.slot} ({itemTypeLabel})</div>
                    <div className={styles.itemStats}>{getStatBonuses(item)}</div>
                    <div className={styles.itemDescription}>{item.description}</div>
                    <div className={styles.itemFooter}>
                      <div className={req.goldMissing ? styles.itemValueMissing : styles.itemValue}>
                        {item.value} gold
                      </div>
                      <button
                        className={styles.buyButton}
                        onClick={() => handlePurchaseItem(item.id)}
                        disabled={loading || !req.canBuy}
                      >
                        {req.goldMissing ? 'Not enough gold' : 'Buy'}
                      </button>
                    </div>
                  </div>
                )
              })}
              {filteredShopItems.length === 0 && (
                <div className={styles.emptyInventory}>No equipment available</div>
              )}
            </div>
          ) : (
            <div className={styles.loading}>Loading shop inventory...</div>
          )}
        </div>
      )}
    </div>
  )
}
