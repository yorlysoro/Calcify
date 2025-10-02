<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Role;
use App\Models\User;

class AdminUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Crear el rol de administrador si no existe
        $adminRole = Role::firstOrCreate(['name' => 'admin']);

        // Crear el usuario administrador si no existe
        $admin = User::firstOrCreate(
            ['email' => 'admin@tusitio.com'],
            [
                'name' => 'Administrator',
                'password' => bcrypt('12345678'), // Cambia la contraseña
            ]
        );

        // Asignar el rol de administrador
        $admin->assignRole($adminRole);
    }
}
